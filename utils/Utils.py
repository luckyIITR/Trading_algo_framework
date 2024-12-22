import uuid
import datetime

class Utils:
    holidays = [
        datetime.date(2024, 12, 25),
        datetime.date(2025, 2, 26),
        datetime.date(2025, 3, 14),
        datetime.date(2025, 3, 31),
        datetime.date(2025, 4, 10),
        datetime.date(2025, 4, 14),
        datetime.date(2025, 4, 18),
        datetime.date(2025, 5, 1),
        datetime.date(2025, 8, 15),
        datetime.date(2025, 8, 27),
        datetime.date(2025, 10, 2),
        datetime.date(2025, 10, 21),
        datetime.date(2025, 10, 22),
        datetime.date(2025, 11, 5),
        datetime.date(2025, 12, 25)
    ]

    @staticmethod
    def generate_trade_id():
        return str(uuid.uuid4())

    @staticmethod
    def get_epoch(datetime_obj):
        # This method converts given datetime_obj to epoch seconds
        epoch_seconds = datetime.datetime.timestamp(datetime_obj)
        return int(epoch_seconds)  # converting double to long

    @staticmethod
    def nearest_strike_price(spot_price, gap):
        return gap * round(spot_price / gap)

    @staticmethod
    def create_options_symbol(exchange, instrument, strike_price, option_type, current_date, expiry_date, expiry_weekday_name):
        monthly_expiry = Utils.get_monthly_expiry(current_date, expiry_weekday_name)
        is_monthly = (monthly_expiry == expiry_date)
        if is_monthly:
            year = str(expiry_date)[2:4]
            month = expiry_date.strftime("%b").upper()
            symbol = exchange + ":" + instrument + year + month + str(strike_price) + option_type.upper()
        else:
            year = str(expiry_date)[2:4]
            month = str(expiry_date)[5:7]
            if month == '10':
                month = 'O'
            elif month == '11':
                month = 'N'
            elif month == '12':
                month = 'D'
            exp_date = str(expiry_date)[-2:]
            symbol = exchange + ":" + instrument + year + month + str(exp_date) + str(strike_price) + option_type.upper()
        return symbol

    @staticmethod
    def get_monthly_expiry(date, weekday_name):
        # Map weekday names to their corresponding integer values (Monday=0, Sunday=6)
        weekdays = {
            "Monday": 0,
            "Tuesday": 1,
            "Wednesday": 2,
            "Thursday": 3,
            "Friday": 4,
            "Saturday": 5,
            "Sunday": 6,
        }

        if weekday_name not in weekdays:
            raise ValueError("Invalid weekday name. Use full names like 'Monday', 'Tuesday', etc.")

        # Extract the year and month from the given date
        year, month = date.year, date.month

        # Get the last day of the month
        if month == 12:
            last_day_of_month = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
        else:
            last_day_of_month = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)

        # Find the last occurrence of the given weekday in the current month
        last_weekday_of_month = last_day_of_month
        while last_weekday_of_month.weekday() != weekdays[weekday_name]:
            last_weekday_of_month -= datetime.timedelta(days=1)

        # Check if the date has already passed
        if date > last_weekday_of_month:
            # If passed, calculate for the next month
            if month == 12:
                next_month = 1
                next_year = year + 1
            else:
                next_month = month + 1
                next_year = year
            last_day_of_next_month = datetime.date(next_year, next_month + 1, 1) - datetime.timedelta(days=1)

            last_weekday_of_next_month = last_day_of_next_month
            while last_weekday_of_next_month.weekday() != weekdays[weekday_name]:
                last_weekday_of_next_month -= datetime.timedelta(days=1)

            # Check if the nearest date is a holiday, and adjust if necessary
            while last_weekday_of_next_month in Utils.holidays:
                last_weekday_of_next_month -= datetime.timedelta(days=1)
            return last_weekday_of_next_month

        # Check if the nearest date is a holiday, and adjust if necessary
        while last_weekday_of_month in Utils.holidays:
            last_weekday_of_month -= datetime.timedelta(days=1)
        return last_weekday_of_month

    @staticmethod
    def get_weekly_expiry(date, weekday_name):
        """
        Calculate the nearest date for the given day of the week.
        Adjusts to the prior day if the nearest date is a holiday.

        Args:
        date (datetime.date): The starting date.
        weekday_name (str): Name of the target day (e.g., "Monday").
        holidays (list): List of datetime.date objects representing holidays.

        Returns:
        datetime.date: The nearest non-holiday date for the target day.
        """
        # Map day names to integers
        day_name_to_int = {
            "Monday": 0,
            "Tuesday": 1,
            "Wednesday": 2,
            "Thursday": 3,
            "Friday": 4,
            "Saturday": 5,
            "Sunday": 6,
        }
        target_day = day_name_to_int[weekday_name]
        days_ahead = target_day - date.weekday()
        if days_ahead < 0:  # If target day already passed this week
            days_ahead += 7
        nearest_date = date + datetime.timedelta(days=days_ahead)

        # Check if the nearest date is a holiday, and adjust if necessary
        while nearest_date in Utils.holidays:
            nearest_date -= datetime.timedelta(days=1)

        return nearest_date
