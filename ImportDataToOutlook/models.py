from ImportDataToOutlook import db

class ExportSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    import_url = db.Column(db.String(500), nullable=False)
    months_back = db.Column(db.Integer, nullable=False)
    months_forward = db.Column(db.Integer, nullable=False)
    venues = db.Column(db.String(1000), nullable=True)  # Comma-separated venue names

    def get_venues(self):
        # Returns a list of venues
        return self.venues.split(',') if self.venues else []
