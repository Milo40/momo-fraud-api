import logging


class LoggerService:
    @staticmethod
    def get_logger(name="custom_logger"):
        """
        Returns a logger instance with the specified name.
        """
        return logging.getLogger(name)


class LogFormatter(logging.Formatter):
    def format(self, record):
        # Dynamically add optional attributes to the message
        custom_attributes = []
        if hasattr(record, "event_code"):
            custom_attributes.append(f"Event Code: {record.event_code}")

        # Add custom attributes to the message, if any
        record.custom = " | ".join(custom_attributes) if custom_attributes else ""

        # Call the parent class's format method
        return super().format(record)
