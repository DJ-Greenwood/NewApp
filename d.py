import os
import csv

def generate_directory_report(directory, output_file="directory_report.csv"):
    """
    Generates a report of all files and folders in the given directory and saves it as a CSV file.
    """
    with open(output_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Folder/File", "Name", "Size (Bytes)", "Last Modified"])

        for root, dirs, files in os.walk(directory):
            # Write folders
            for folder in dirs:
                folder_path = os.path.join(root, folder)
                writer.writerow(["Folder", folder, "", ""])

            # Write files
            for filename in files:
                file_path = os.path.join(root, filename)
                size = os.path.getsize(file_path)
                modified_time = os.path.getmtime(file_path)
                writer.writerow(["File", filename, size, modified_time])

    print(f"Directory report saved as {output_file}")

# Example usage
directory_path = "D:/Business/localMIF/app/ai_chat"  # Change this to your target directory
generate_directory_report(directory_path)
