# DW Site Tools

A package for [Sublime Text 3](https://www.sublimetext.com/3) that allows import/export of Adobe Dreamweaver™ site settings files (.STE) into Sublime Text projects.

(S)FTP settings can be exported to/from sftp-config.json files for the [Sublime SFTP package](https://wbond.net/sublime_packages/sftp).

## Scope of this package
I created this plugin to help my coworkers transition from Adobe Dreamweaver™ to Sublime Text, and to familiarize myself with the Sublime Text package API.

Because I stopped using Dreamweaver™ years ago and their site definitions format is proprietary, this plugin might break on future versions if there are changes to the .STE format. It has not been tested with any Dreamweaver™ versions newer than 12.

Use cases might be slim, but I decided to make this package available to the community nonetheless.

## Support for Sublime Text 2
Basic support for Sublime Text 2 is implemented, but not well tested. Use at your own risk! 

## Installation

Please use [Package Control](https://sublime.wbond.net/installation) to install this plugin. Manual installation is of course possible if you want to modify the source code, but as an end user, Package Control is your best option to ensure you will always get the latest updates.

## Using the plugin

### Per-project settings
DW Site Tools stores its settings on a per-project basis in your .sublime-project file. Therefore, saving your project before running the import/export commands is mandatory.

If you want to modify the settings by hand, search for the "dwst" key in the project’s .sublime-project file.

### Settings setup
Run the command **DW Site Tools: Configure export settings...** either from the command palette (Ctlr+Shift+P), or from the menu: **Project > DW Site Tools**.

During setup, the plugin will look for a sftp-config.json file in your project root (if your project contains more than one directory, each of them will be searched until a matching file is found) and ask you if you want to import settings from there.

### Importing an existing .STE file
To import project settings and/or (S)FTP configuration from a Dreamweaver™ .STE file, run the command **DW Site Tools: Import existing .ste** from the command palette or the menu: **Project > DW Site Tools**.

Enter the full path to the file you want to import.

This will update settings in your .sublime-project file, as well as create a new sftp-config.json file in your project root or update an existing one.

### Exporting project settings to .STE
Run **DW Site Tools: Export .ste file** from the command palette or the menu: **Project > DW Site Tools**.

Enter the full path to the export file.

## Helping to improve this package
Contributions are always welcome. If you find a bug while importing a .STE file created by a more recent version of Dreamweaver™, please open an issue and make sure to include the .STE file (don’t forget to remove sensitive data, like passwords, before submitting!).
