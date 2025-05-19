"""
Routes and views for the flask application.
"""

from datetime import datetime, timedelta
from flask import render_template, request, redirect, url_for, flash, jsonify
from ImportDataToOutlook import app, db
from ImportDataToOutlook.models import ExportSetting
import requests
from lxml import etree
from flask import session
import os

@app.before_request
def create_tables():
    # Ensure all database tables are created before the first request
    # Don't run Timewise when running this app, it doesn't work when Open VPN GUI is running! 
    db.create_all()

@app.route('/')
@app.route('/home')
def home():
    """Renders the home page."""
    return render_template(
        'index.html',
        title='Home Page',
        year=datetime.now().year,
    )

@app.route('/contact')
def contact():
    """Renders the contact page."""
    return render_template(
        'contact.html',
        title='Contact',
        year=datetime.now().year,
        message='Your contact page.'
    )

@app.route('/about')
def about():
    """Renders the about page."""
    return render_template(
        'about.html',
        title='About',
        year=datetime.now().year,
        message='Your application description page.'
    )

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if not session.get('settings_authenticated'):
        return redirect(url_for('settings_login'))
    venues = []
    sample_url = request.args.get('sample_url')
    if sample_url:
        try:
            resp = requests.get(sample_url)
            root = etree.fromstring(resp.content)
            venues = list({row.get('venuevenuename') for row in root.findall('.//row') if row.get('venuevenuename')})
        except Exception:
            venues = []

    # Initialize variables
    name = None
    import_url = None
    months_back = 0
    months_forward = 0
    selected_venues = []

    if request.method == 'POST':
        # Get form data
        edit_id = request.form.get('edit_id')
        name = request.form.get('name')
        import_url = request.form.get('import_url')
        months_back = int(request.form.get('months_back', 0))
        months_forward = int(request.form.get('months_forward', 0))
        selected_venues = request.form.getlist('venues')

        if not name or not import_url:
            flash('Name and Import URL is required.', 'danger')
            return redirect(url_for('settings'))

        if edit_id:  # Update existing export
            export = ExportSetting.query.get(edit_id)
            if export:
                export.name = name
                export.import_url = import_url
                export.months_back = months_back
                export.months_forward = months_forward
                export.venues = ','.join(selected_venues)
                db.session.commit()
                flash('Export setting updated!')
            else:
                flash('Export not found.', 'danger')
        else:  # Create new export
            export = ExportSetting(
                name=name,
                import_url=import_url,
                months_back=months_back,
                months_forward=months_forward,
                venues=','.join(selected_venues)
            )
            db.session.add(export)
            db.session.commit()
            flash('Export setting saved!')
        return redirect(url_for('settings'))

    exports = ExportSetting.query.all()
    return render_template('settings.html', venues=venues, exports=exports)

@app.route('/delete_export/<int:export_id>', methods=['POST'])
def delete_export(export_id):
    """
    Deletes the export with the given ID.
    """
    export = ExportSetting.query.get(export_id)
    if export:
        db.session.delete(export)
        db.session.commit()
        flash('Export deleted!', 'success')
    else:
        flash('Export not found.', 'danger')
    return redirect(url_for('settings'))

@app.route('/get_venues_from_xml', methods=['POST'])
def get_venues_from_xml():
    """
    Receives a POST request with a JSON body containing an 'url' key.
    Fetches the XML from the given URL, extracts unique venue names,
    sorts them alphabetically, and returns them as a JSON response.
    """
    url = request.json.get('url')
    if not url:
        return jsonify({'venues': []})
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        root = etree.fromstring(resp.content)
        venues = set()
        for row in root.findall('.//row'):
            name = row.get('venuevenuename')
            if name:
                venues.add(name)
        venues = sorted(venues, key=lambda s: s.lower())
        return jsonify({'venues': venues})
    except Exception as e:
        return jsonify({'venues': [], 'error': str(e)})

@app.route('/get_export_venues/<int:export_id>')
def get_export_venues(export_id):
    """
    Returns the list of venues for a given export as a JSON response.
    Assumes that ExportSetting.venues is a comma-separated string.
    """
    export = ExportSetting.query.get(export_id)
    if not export or not export.venues:
        return jsonify({'venues': []})
    venues = [v.strip() for v in export.venues.split(',') if v.strip()]
    return jsonify({'venues': venues})

@app.route('/show_export_data/<int:export_id>')
def show_export_data(export_id):
    """
    Shows filtered data for a specific export configuration.
    """
    export = ExportSetting.query.get_or_404(export_id)
    filtered_rows = []
    try:
        resp = requests.get(export.import_url)
        root = etree.fromstring(resp.content)
        now = datetime.now()
        start_date = now - timedelta(days=30 * export.months_back)
        end_date = now + timedelta(days=30 * export.months_forward)
        venues = export.get_venues()
        for row in root.findall('.//row'):
            # Filter by venue if venues are specified
            if venues and row.get('venuevenuename') not in venues:
                continue
            # Filter by date
            starttime = row.get('starttime')
            endtime = row.get('endtime')
            if not starttime or not endtime:
                continue
            dt_start = datetime.fromisoformat(starttime)
            dt_end = datetime.fromisoformat(endtime)
            if dt_end < start_date or dt_start > end_date:
                continue
            # Only include fields that are not empty
            filtered_rows.append({
                'starttime': starttime,
                'endtime': endtime,
                'activityname': row.get('activityname') or '',
                'subject': row.get('subject') or '',
                'venuevenuename': row.get('venuevenuename') or '',
                'appointmentstatusname': row.get('appointmentstatusname') or '',
                'timewise_ido': 'Timewise IDO'
            })
    except Exception as e:
        flash(f'Error fetching or parsing data: {e}')
        filtered_rows = []

    # Always sort by starttime (ascending)
    filtered_rows.sort(key=lambda row: row['starttime'])

    return render_template('show_export_data.html', export=export, rows=filtered_rows)

from flask import Response

@app.route('/calendar_export/<int:export_id>.ics')
def calendar_export(export_id):
    export = ExportSetting.query.get_or_404(export_id)
    filtered_rows = []
    try:
        resp = requests.get(export.import_url)
        root = etree.fromstring(resp.content)
        now = datetime.now()
        start_date = now - timedelta(days=30 * export.months_back)
        end_date = now + timedelta(days=30 * export.months_forward)
        venues = export.get_venues()
        for row in root.findall('.//row'):
            if venues and row.get('venuevenuename') not in venues:
                continue
            starttime = row.get('starttime')
            endtime = row.get('endtime')
            if not starttime or not endtime:
                continue
            dt_start = datetime.fromisoformat(starttime)
            dt_end = datetime.fromisoformat(endtime)
            if dt_end < start_date or dt_start > end_date:
                continue
            filtered_rows.append({
                'starttime': dt_start,
                'endtime': dt_end,
                'activityname': row.get('activityname') or '',
                'subject': row.get('subject') or '',
                'venuevenuename': row.get('venuevenuename') or '',
                'appointmentstatusname': row.get('appointmentstatusname') or '',
            })
    except Exception as e:
        return Response(f"Error: {e}", status=500)

    # Generate ICS content
    ics_lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//YourApp//EN"
]
    now_utc = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    for idx, row in enumerate(filtered_rows):
        uid = f"{row['starttime'].strftime('%Y%m%dT%H%M%S')}-{idx}@yourapp"
        ics_lines.extend([
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{now_utc}",
        f"DTSTART:{row['starttime'].strftime('%Y%m%dT%H%M%S')}",
        f"DTEND:{row['endtime'].strftime('%Y%m%dT%H%M%S')}",
        f"SUMMARY:{row['activityname'] or row['subject'] or 'Event'}",
        f"LOCATION:{row['venuevenuename']}",
        f"DESCRIPTION:{row['appointmentstatusname']}",
        "END:VEVENT"
    ])
    ics_lines.append("END:VCALENDAR")
    ics_content = "\r\n".join(ics_lines)

    return Response(ics_content, mimetype='text/calendar')

@app.route('/settings_login', methods=['GET', 'POST'])
def settings_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == os.getenv('SETTINGS_PASSWORD'):
            session['settings_authenticated'] = True
            return redirect(url_for('settings'))
        else:
            flash('Incorrect password.', 'danger')
    return render_template('settings_login.html')

@app.route('/settings_logout')
def settings_logout():
    session.pop('settings_authenticated', None)
    flash('Logged out.', 'info')
    return redirect(url_for('settings_login'))