"""
Module configuration custom logger.
"""
import logging
import logging.config
import os

class AppLogger:
    def __init__(self, project_name, config_file='logging.ini'):
        # Check if the configuration file exists
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Logging configuration file '{config_file}' not found.")
        
        # Load the logging configuration from the file
        logging.config.fileConfig(config_file)
        
        # Create a logger instance
        self.logger = logging.getLogger('appLogger')
        
        # Add the project name to the logger
        for handler in self.logger.handlers:
            handler.addFilter(ProjectNameFilter(project_name))
    
    def get_logger(self):
        return self.logger

class ProjectNameFilter(logging.Filter):
    def __init__(self, project_name):
        self.project_name = project_name
    
    def filter(self, record):
        record.project_name = self.project_name
        return True

def create_logger() -> logging.Logger:
    """
    Initialize logger for project.
    """
    project_name = 'ChatBot'
    return AppLogger(project_name).get_logger()


logger = create_logger()
# # Example usage
# if __name__ == "__main__":
#     logger = ProjectLogger().get_logger()
#     logger.debug("This is a debug message")
#     logger.info("This is an info message")
#     logger.warning("This is a warning message")
#     logger.error("This is an error message")
#     logger.critical("This is a critical message")