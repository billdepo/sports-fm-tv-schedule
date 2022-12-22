Parse Sports TV events from https://www.sport-fm.gr/tv on a daily basis.

This project scrapes https://www.sport-fm.gr/tv to get each day's sports events that are of interest and then creates a single Google Calendar event on a selected calendar.

Example event:

    Title: Sport Events Tournaments: Euroleague, Λιγκ Καπ Αγγλίας
    Date: Friday, December 23, 10:00 – 10:01
    Description: 
    Φενέρμπαχτσε - Παρτίζαν | Euroleague @ 19:45, NOVASPORTS 4
    Αλμπα Βερολίνου - Μακάμπι Τελ Αβίβ | Euroleague @ 21:00, NOVASPORTS 5
    Ολυμπιακός - Ερυθρός Αστέρας | Euroleague @ 21:00, Novasports Prime
    Μπασκόνια - Βίρτους Μπολόνια | Euroleague @ 21:30, Novasports Start
    Μάντσεστερ Σίτι - Λίβερπουλ | Λιγκ Καπ Αγγλίας @ 21:50, Action 24
    Μάντσεστερ Σίτι - Λίβερπουλ | Λιγκ Καπ Αγγλίας @ 22:00, Action 24
    Ρεάλ Μαδρίτης - Βιλερμπάν | Euroleague @ 22:00, NOVASPORTS 4


![Alt text](example_event.PNG "Google Calendar sample event")

and create a single calendar entry that contains all the events of interest 