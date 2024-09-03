import os
import zipfile
import sys
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox, QCheckBox, QVBoxLayout, QDialog, QDialogButtonBox
import shutil

def extract_zip_with_structure(zip_filename, extract_to, folders_to_extract):
    """Extract files from the zip file to maintain the internal folder structure."""
    with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
        all_members = zip_ref.namelist()
        print(f"All members in the ZIP: {all_members}")

        for member in all_members:
            if member.endswith('/'):
                continue  # Skip directories in the ZIP file listing

            normalized_path = os.path.normpath(member)  # Normalize path for consistent matching
            folder_name = normalized_path.split(os.sep)[0]  # Get top-level folder name
            
            print(f"Checking if '{normalized_path}' should be extracted...")

            # Check if the top-level folder is in the list of folders to extract
            if folder_name in folders_to_extract:
                # Remove the top-level folder from the path
                internal_path = os.path.join(*normalized_path.split(os.sep)[1:])
                target_path = os.path.join(extract_to, internal_path)

                print(f"Extracting '{normalized_path}' to '{target_path}'")  # Debugging output

                os.makedirs(os.path.dirname(target_path), exist_ok=True)

                try:
                    with zip_ref.open(member) as source, open(target_path, "wb") as target:
                        shutil.copyfileobj(source, target)
                    print(f"Successfully extracted '{normalized_path}' to '{target_path}'")
                except Exception as e:
                    print(f"Failed to extract '{member}': {e}")

def main():
    app = QApplication([])

    QMessageBox.information(None, 'Instructions', 'Please select the installation folder of the game you are modding.')

    extract_to = QFileDialog.getExistingDirectory(None, 'Jish_Pack - Select Installation Directory', '')

    if extract_to:
        try:
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
                zip_filename = os.path.join(base_path, 'mod_pack.zip')
            else:
                zip_filename = 'mod_pack.zip'

            print(f"Using ZIP file: {zip_filename}")

            essential_folders = {essential_folders}  # Ensure this is correctly populated

            dialog = QDialog()
            dialog.setWindowTitle('Select Optional Folders')
            layout = QVBoxLayout(dialog)

            with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
                all_folders = set()
                for member in zip_ref.namelist():
                    if '/' in member:
                        top_level_dir = member.split('/')[0]
                        all_folders.add(top_level_dir)

                optional_folders = all_folders - set(essential_folders)

            checkboxes = [QCheckBox(option) for option in sorted(optional_folders)]

            for checkbox in checkboxes:
                layout.addWidget(checkbox)

            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)

            if dialog.exec_() == QDialog.Accepted:
                selected_folders = [checkbox.text() for checkbox in checkboxes if checkbox.isChecked()]

                print(f"Selected folders for extraction: {selected_folders}")

                # Call the function to extract and maintain internal folder structure
                extract_zip_with_structure(zip_filename, extract_to, list(set(essential_folders) | set(selected_folders)))

                QMessageBox.information(None, 'Success', f'Mod pack installed successfully to: {extract_to}')
            else:
                QMessageBox.warning(None, 'Warning', 'Installation cancelled.')
        except Exception as e:
            QMessageBox.critical(None, 'Error', f'Failed to install mod pack: {str(e)}')
    else:
        QMessageBox.warning(None, 'Warning', 'No installation directory selected.')

if __name__ == "__main__":
    main()
