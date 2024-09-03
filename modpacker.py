import os
import sys
import zipfile
import shutil
import tempfile
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QMessageBox, QProgressBar, QComboBox, QListWidget, QListWidgetItem
from PyQt5.QtCore import Qt

def create_zip_from_folder(source_dir, output_filename, compression_method, essential_folders, progress_callback=None):
    """Compress the source directory into a ZIP file with the specified compression method."""
    total_files = sum(len(files) for _, _, files in os.walk(source_dir))
    processed_files = 0
    
    with zipfile.ZipFile(output_filename, 'w', compression=compression_method) as zipf:
        for root, _, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start=source_dir)
                
                # Add metadata to mark folders as essential or optional
                is_essential = any(folder in arcname for folder in essential_folders)
                zipf.write(file_path, arcname, compress_type=compression_method, compresslevel=9)
                
                processed_files += 1

                # Update progress
                if progress_callback:
                    progress = int((processed_files / total_files) * 100)
                    progress_callback(progress)

def create_mod_pack(mod_folder_path, output_filename, compression_method, essential_folders, progress_callback=None):
    """Create a ZIP file and an extractor Python script, then package them into an EXE."""

    # Define output filenames
    zip_filename = 'mod_pack.zip'
    extractor_script_filename = 'extractor.py'

    # Create a ZIP file from the mod folder with progress callback
    create_zip_from_folder(mod_folder_path, zip_filename, compression_method, essential_folders, progress_callback)

    # Check if running as a PyInstaller bundle
    if getattr(sys, 'frozen', False):
        # Running in a PyInstaller bundle
        base_path = sys._MEIPASS
        extractor_template_path = os.path.join(base_path, 'extractor_template.py')
    else:
        # Running in a normal Python environment
        extractor_template_path = 'extractor_template.py'

    # Read the external extractor script template
    with open(extractor_template_path, 'r') as file:
        extractor_script_content = file.read()

    # Replace placeholders in the script content
    extractor_script_content = extractor_script_content.replace("{essential_folders}", str(essential_folders))

    # Write the customized extractor script to a file
    with open(extractor_script_filename, 'w') as f:
        f.write(extractor_script_content)

    print(f"Packaging extractor script and ZIP into a single EXE...")

    # Package the extractor script and ZIP file into a single EXE using PyInstaller
    os.system(f'pyinstaller --onefile --add-data "{zip_filename};." --name "{output_filename}" "{extractor_script_filename}"')

    # Clean up temporary files
    os.remove(zip_filename)
    os.remove(extractor_script_filename)
    shutil.rmtree('build', ignore_errors=True)
    shutil.rmtree('__pycache__', ignore_errors=True)
    
    # Remove the .spec file if it exists
    spec_filename = f'{output_filename}.spec'
    if os.path.exists(spec_filename):
        os.remove(spec_filename)

    print(f"Mod pack EXE created successfully as '{output_filename}' in the 'dist' directory!")

    # Open the dist directory in the file explorer
    dist_path = os.path.join(os.getcwd(), 'dist')
    if os.path.exists(dist_path):
        if os.name == 'nt':  # for Windows
            os.startfile(dist_path)
        elif os.name == 'posix':  # for MacOS and Linux
            subprocess.Popen(['open', dist_path])
        else:
            print(f"Please open the '{dist_path}' directory manually.")

class ModPackGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.mod_folder_path = ""
        self.initUI()

    def initUI(self):
        # Set up the GUI layout
        layout = QVBoxLayout()

        self.label = QLabel('Select the mod folder:')
        layout.addWidget(self.label)

        # Button to select mod folder
        self.btn_select_mod_folder = QPushButton('Select Mod Folder', self)
        self.btn_select_mod_folder.clicked.connect(self.select_mod_folder)
        layout.addWidget(self.btn_select_mod_folder)

        # List widget to select essential folders
        self.essential_folders_list = QListWidget(self)
        self.essential_folders_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(QLabel('Select Essential Folders:'))
        layout.addWidget(self.essential_folders_list)

        # Dropdown for compression method
        self.compression_dropdown = QComboBox(self)
        self.compression_dropdown.addItem('LZMA', zipfile.ZIP_LZMA)
        self.compression_dropdown.addItem('Deflated', zipfile.ZIP_DEFLATED)
        self.compression_dropdown.addItem('Stored (No Compression)', zipfile.ZIP_STORED)
        layout.addWidget(QLabel('Select Compression Method:'))
        layout.addWidget(self.compression_dropdown)

        # Button to create mod pack
        self.btn_create_mod_pack = QPushButton('Create Mod Pack', self)
        self.btn_create_mod_pack.clicked.connect(self.create_mod_pack)
        layout.addWidget(self.btn_create_mod_pack)

        # Progress bar for mod pack creation
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Button for help
        self.btn_help = QPushButton('Help', self)
        self.btn_help.clicked.connect(self.show_help)
        layout.addWidget(self.btn_help)

        # Set main window properties
        self.setLayout(layout)
        self.setWindowTitle('Mod Pack Creator')
        self.setGeometry(300, 300, 400, 300)  # Adjust height to fit the new list widget

    def select_mod_folder(self):
        # Open file dialog to select mod folder
        folder = QFileDialog.getExistingDirectory(self, 'Select Mod Folder')
        if folder:
            self.mod_folder_path = folder
            self.label.setText(f'Mod Folder Selected: {folder}')
            self.populate_folders_list()

    def populate_folders_list(self):
        # Populate the list widget with folders in the selected mod folder
        self.essential_folders_list.clear()
        for folder_name in os.listdir(self.mod_folder_path):
            folder_path = os.path.join(self.mod_folder_path, folder_name)
            if os.path.isdir(folder_path):
                item = QListWidgetItem(folder_name)
                item.setCheckState(Qt.Unchecked)
                self.essential_folders_list.addItem(item)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def create_mod_pack(self):
        # Check if path is set
        if not self.mod_folder_path:
            QMessageBox.warning(self, 'Warning', 'Please select a mod folder.')
            return

        # Determine which folders are essential
        essential_folders = [item.text() for item in self.essential_folders_list.findItems('*', Qt.MatchWildcard) if item.checkState() == Qt.Checked]

        output_filename = os.path.basename(self.mod_folder_path)
        compression_method = self.compression_dropdown.currentData()

        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            create_mod_pack(self.mod_folder_path, output_filename, compression_method, essential_folders, self.update_progress)
            QMessageBox.information(self, 'Success', f'Mod pack EXE created successfully as {output_filename}!')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to create mod pack: {str(e)}')
        finally:
            self.progress_bar.setVisible(False)

    def show_help(self):
        # Help message content
        help_text = (
            "Mod Pack Creator Application\n\n"
            "This application allows you to create a mod pack from a folder of mod files.\n\n"
            "Each mod/module should be created within its own pack folder.\n\n"
            "For example, ModPack1 folder would contain subfolders with mods.\n\n"
            "Steps to use the application:\n"
            "1. Click 'Select Mod Folder' to choose the folder containing your mod files.\n"
            "2. Click 'Create Mod Pack' to generate an executable to install the mod pack\n"
        )
        QMessageBox.information(self, 'Help', help_text)

def main():
    app = QApplication([])
    gui = ModPackGUI()
    gui.show()
    app.exec_()

if __name__ == "__main__":
    main()