# Timewise IDO

**Timewise IDO** is a web application that lets you import, filter, and export calendar data from the Timewise Export Module, making it easy to display and keep your data up-to-date in Outlook or any other calendar software that supports iCal/ICS feeds.

## Features

- **Import Data:** Fetch data from Timewise using the "Lokal Venue Appointment With Venue" export.
- **Flexible Filtering:** Create multiple exports with custom filters for date ranges and venues.
- **Live Calendar Feeds:** Generate unique iCal/ICS URLs for each export, allowing Outlook and other calendar clients to subscribe and always receive the latest data.
- **Easy Management:** Edit, delete, and preview your exports directly from the web interface.

## How It Works

1. **Import:** Paste your Timewise export URL into the app.
2. **Filter:** Set your desired date range and select venues to filter the data.
3. **Export:** Use the generated iCal/ICS link to subscribe in Outlook or any compatible calendar app. The feed updates automatically with the latest data from Timewise.

## Requirements

- Python 3.x
- Flask
- lxml
- requests
- (See `requirements.txt` for full list)

## Getting Started

1. Clone the repository.
2. Install dependencies:  
   `pip install -r requirements.txt`
3. Run the application:  
   `flask run`
4. Open your browser and go to `http://localhost:5000`

## License

MIT License
