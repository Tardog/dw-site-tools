'''
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import sublime
import sublime_plugin
import os
import sys
import json
import ast
import xml.etree.ElementTree as ET

from os.path import dirname, realpath, expanduser
from os.path import join

sys.path.append(os.path.join(os.path.dirname(__file__), "lib", "tkinter"))


# Determine version of ST and import modules accordingly
st_version = 2

if int(sublime.version()) > 3000:
    st_version = 3

if st_version == 2:
    # Attempt to fix a problem with ST2 not properly loading the xml library on linux
    if sys.platform.startswith('linux'):
        py2_7 = "/usr/lib/python2.7/lib-dynload/"
        py2_6 = "/usr/lib/python2.6/lib-dynload/"

        if os.path.isdir(py2_7):
            py_dir = py2_7
        elif os.path.isdir(py2_6):
            py_dir = py2_6
        else:
            sublime.error_message = 'DW Site Tools was unable to find the Python 2.6 library path in /usr/lib. Is your system version of Python too old? (< 2.6)'

        sys.path.append(py_dir)
elif st_version != 3:
    sublime.error_message = 'You are running an outdated version of Sublime Text. Please updated your installation.'


# Create Dreamweaver sites from ST project
class DwstAddSettingsCommand(sublime_plugin.WindowCommand):

    def run(self):
        if hasattr(self.window, 'folders'):
            self.project_data = self.window.project_data()

            if st_version == 3:
                self.project_folders = self.window.folders()

            if self.import_settings():
                sublime.message_dialog("Settings saved to current project.")
            else:
                sublime.message_dialog("Importing default settings failed!")
        else:
            sublime.error_message('Before running this command, please add at least one folder to your project.')

    def import_settings(self):
        # Prompt for sftp-config.json import
        settings = self.prompt_sublime_sftp()

        return dwst_settings_setup(settings)

    def prompt_sublime_sftp(self):
        answer = sublime.ok_cancel_dialog("Import remote settings from sftp-config.json?", "Yes")

        if answer:
            config_json = self.read_sftp_config()

            # Import remote settings and start sitemap generation
            if config_json:
                return self.import_remote_config(config_json)
            else:
                sublime.error_message('Failed to read the settings in sftp-config.json')
        else:
            return False

    # Get settings from sftp-config.json
    def read_sftp_config(self):
        if not self.project_folders:
            return False

        for folder in self.project_folders:
            try:
                f = open(folder + '/sftp-config.json')
            except IOError:
                return False

            return f.read()
            break

    # Import remote settings from sftp-config.json
    def import_remote_config(self, config_json):
        sftp_config = {}

        # Strip comments from the json string
        config_json = dwst_strip_json_comments(config_json)

        try:
            settings = json.loads(config_json)
        except ValueError as e:
            return False

        try:
            # Minimum required settings
            sftp_config['remote_path'] = settings['remote_path']
            sftp_config['hostname'] = settings['host']
            sftp_config['remote_user'] = settings['user']
            sftp_config['remote_password'] = settings['password']
            sftp_config['auto_upload'] = str(settings['upload_on_save'])
            sftp_config['checkout_when_open'] = str(settings['sync_down_on_open'])

            # Assume SFTP if the setting is not present
            if 'type' not in settings:
                sftp_config['access_type'] = 'sftp'
            else:
                sftp_config['access_type'] = settings['type']

            # Set passive mode to false if not present in the settings
            if 'passive_mode' not in settings:
                sftp_config['passive_mode'] = 'FALSE'
            else:
                sftp_config['passive_mode'] = str(settings['ftp_passive_mode'])

        except KeyError as e:
            sublime.error_message('One of the required settings is missing in sftp-config.json: ' + str(e))
            return False

        return sftp_config


# Create Dreamweaver sites from project settings
class DwstGenerateSiteCommand(sublime_plugin.WindowCommand):

    def run(self):
        try:
            data = self.window.project_data()
            self.project_folders = self.window.folders()

            if not data['dwst']:
                raise KeyError

        except KeyError:
            sublime.error_message('Unable to find the settings required for site generation. Please run the command "Configure export settings", then try again.')
            return False

        self.config = data['dwst']
        self.create_site_file()

    # Create the .ste file
    def create_site_file(self):
        default_path = self.project_folders[0] + os.sep + 'example.ste'
        self.window.show_input_panel("Path/filename", default_path, self.save_ste_file, None, None)
        return False

    # Write the site file
    def save_ste_file(self, path):
        content = self.insert_settings_into_xml()

        try:
            f = open(path, 'w')
            f.write(content)
            f.close()
        except IOError as e:
            sublime.error_message('An error occured while writing the site file: ' + str(e))
            raise

        sublime.message_dialog("Export successful.")

    # Combine the config settings with the default .ste template
    def insert_settings_into_xml(self):
        # Load the .ste template from the current plugin dir
        try:
            tree = ET.parse(plugin_dir + os.sep + 'default.ste')
            root = tree.getroot()

            # Insert settings
            for localinfo in root.findall('localinfo'):
                localinfo.set("sitename", str(self.config['site_name']))
                localinfo.set("localroot", str(self.config['site_root']))
                localinfo.set("imagefolder", str(self.config['image_folder']))
                localinfo.set("httpaddress", str(self.config['remote_url']))

            for serverlist in root.findall('serverlist'):
                for server in serverlist:
                    server.set("weburl", str(self.config['remote_url']))
                    server.set("accesstype", str(self.config['access_type']))
                    server.set("host", str(self.config['hostname']))
                    server.set("name", str(self.config['hostname']))
                    server.set("remoteroot", str(self.config['remote_path']))
                    server.set("user", str(self.config['remote_user']))
                    server.set("pw", dwst_encode_password(str(self.config['remote_password'])))
                    server.set("autoUpload", str(self.config['auto_upload']))
                    server.set("checkoutwhenopen", str(self.config['checkout_when_open']))
                    server.set("usepasv", str(self.config['passive_mode']))

                    if self.config['access_type'] == 'sftp':
                        server.set("useSFTP", 'TRUE')

                    if self.config['access_type'] == 'ftps':
                        server.set("useFTPS", 'TRUE')

        except Exception as e:
            sublime.error_message('Error while parsing the .ste template: ' + str(e))
            raise

        try:
            if st_version == 3:
                xml_string = ET.tostring(root, "unicode")
            else:
                xml_string = ET.tostring(root)

        except Exception as e:
            sublime.error_message('Error while parsing the .ste template: ' + str(e))
            raise

        return '<?xml version="1.0" encoding="utf-8" ?>\n' + xml_string


# Edit the current project data
class DwstEditSettingsCommand(sublime_plugin.TextCommand):

    def run(self, edit, UserData=None):
        self.edit = edit


# Import settings from .ste file
class DwstImportSiteCommand(sublime_plugin.WindowCommand):

    def run(self):
        self.request_path()
        self.imported = {}
        self.project_data = self.window.project_data()

    def request_path(self):
        default_path = dwst_default_file_path() + os.sep + "example.ste"
        # root = tk.Tk()
        # file_path = filedialog.askopenfilename()
        self.window.show_input_panel("File location", default_path, self.load_ste_file, None, None)

    def load_ste_file(self, path):
        if not path:
            sublime.error_message("Please enter the full path to your .ste file, including the filename. Press ESC to abort.")
            self.request_path()

        # Attempt to parse the file from disk
        try:
            tree = ET.parse(path)
            root = tree.getroot()
        except FileNotFoundError as e:
            sublime.error_message("Error while opening .ste: File not found.")
        except Exception as e:
            sublime.error_message("Error while opening .ste:" + str(e))

        # Load settings from XML
        self.load_xml_settings(root)

        # Call global function to import settings
        if (dwst_settings_setup(self.imported)):
            sublime.message_dialog("File import successful!")
        else:
            sublime.error_message("File import failed!")

    def load_xml_settings(self, root):
        try:
            for localinfo in root.findall('localinfo'):
                self.imported["site_name"] = localinfo.get("sitename")
                self.imported["site_root"] = localinfo.get("localroot")
                self.imported["image_folder"] = localinfo.get("imagefolder")
                self.imported["remote_url"] = localinfo.get("httpaddress")

            for serverlist in root.findall('serverlist'):
                for server in serverlist:
                    self.imported["remote_url"] = server.get("weburl")
                    self.imported["access_type"] = server.get("accesstype")
                    self.imported["hostname"] = server.get("host")
                    self.imported["remote_path"] = server.get("remoteroot")
                    self.imported["remote_user"] = server.get("user")
                    self.imported["remote_password"] = dwst_decode_password(server.get("pw"))
                    self.imported["auto_upload"] = server.get("autoUpload")
                    self.imported["checkout_when_open"] = server.get("checkoutwhenopen")
                    self.imported["passive_mode"] = server.get("usepasv")
                    self.imported["access_type"] = server.get("useSFTP")
                    self.imported["access_type"] = server.get("useFTPS")

        except Exception as e:
            sublime.error_message('Error while parsing the .ste file: ' + str(e))
            raise


# Global functions
window = sublime.active_window()
project_folders = window.folders
plugin_dir = dirname(realpath(__file__))


def dwst_default_file_path():
    folders = window.folders()

    if not folders:
        return expanduser("~")
    else:
        return folders[0]


# Remove all lines starting with // from a string
def dwst_strip_json_comments(text):
    lines = text.split("\n")
    newlines = []

    for x, line in enumerate(lines):
        line = line.strip()
        if not line.startswith("//"):
            newlines.append(line)

    # Get rid of any trailing comma before the closing bracket
    return ''.join(newlines).replace(',}', '}')


# Encode a string with Dreamweaver password "encryption"
def dwst_encode_password(input):
    top = 0
    output = ''

    for i, char in enumerate(input):
        currentChar = ord(char)
        if currentChar < 0 or currentChar > 0xFFFF:
            return False

        if top != 0:
            if 0xDC00 <= currentChar and currentChar <= 0xDFFF:
                output += hex(0x10000 + ((top - 0xD800) << 10) + (currentChar - 0xDC00) + i)
                top = 0
                continue
            else:
                return False

        if 0xD800 <= currentChar and currentChar <= 0xDBFF:
            top = currentChar
        else:
            output += hex(currentChar + i)

    return output.replace('0x', '').upper()


# Decode a Dreamweaver password into a string
def dwst_decode_password(input):
    output = ""
    length = len(input)

    if length == 0:
        return ""

    for i in range(int(length / 2)):
        start = i * 2
        end = start + 2
        currentHex = int(input[start:end], 16)

        if currentHex <= 0xFFFF:
            output += chr(currentHex - i)
        elif currentHex <= 0x10FFFF:
            currentHex -= 0x10000
            output += chr(0xD800 | (currentHex >> 10)) + chr(0xDC00 | (currentHex & 0x3FF) - i)
        else:
            return False

    return output


def dwst_settings_setup(imported):
    # Test if plugin specific settings exist in project
    project_data = window.project_data()

    if 'dwst' not in project_data:
        # Read default settings
        try:
            with open(join(sublime.packages_path(), "DW Site Tools") + '/dw-site-tools.default-config') as f:
                raw = f.read()

                # Convert settings string into a dictionary
                settings = ast.literal_eval(raw)

        except IOError:
            sublime.error_message("Error while trying to parse default settings. Please reinstall the plugin.")
            return False
    else:
        # Get current settings
        settings = project_data['dwst']

    # Set site name to name of current project
    project_file_name = window.project_file_name()
    if not project_file_name:
        sublime.error_message("Please save your project before running this command.")
        return False

    try:
        settings['site_name'] = os.path.splitext(os.path.split(project_file_name)[1])[0]
    except Exception:
        raise

    if hasattr(project_folders, 'folders'):
        settings['site_root'] = project_folders[0]

    # Find and replace imported settings
    if imported:
        for k, v in imported.items():
            settings[k] = v

    # Add settings to project data
    project_data['dwst'] = settings

    # Save new project data and open the project file for editing
    window.set_project_data(project_data)
    settings = window.open_file(window.project_file_name())
    settings.run_command("dwst_edit_settings")

    return True
