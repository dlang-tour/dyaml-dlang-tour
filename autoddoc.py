#!/usr/bin/python3 

# License: Boost 1.0
#
# Copyright (c) 2011 Ferdinand Majerech
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import argparse
import configparser
import os
import os.path
import re
import shutil
import subprocess


template_macros =\
("PBR              = <div class=\"pbr\">$0</div>\n"
 "BR               = <br>\n"
 "DDOC_DITTO       = $(BR)$0\n"
 "DDOC_SUMMARY     = $(P $0)\n"
 "DDOC_DESCRIPTION = $(P $0)\n"
 "DDOC_AUTHORS     = $(B Authors:)$(PBR $0)\n"
 "DDOC_BUGS        = $(RED BUGS:)$(PBR $0)\n"
 "DDOC_COPYRIGHT   = $(B Copyright:)$(PBR $0)\n"
 "DDOC_DATE        = $(B Date:)$(PBR $0)\n"
 "DDOC_DEPRECATED  = $(RED Deprecated:)$(PBR $0)\n"
 "DDOC_EXAMPLES    = $(B Examples:)$(PBR $0)\n"
 "DDOC_HISTORY     = $(B History:)$(PBR $0)\n"
 "DDOC_LICENSE     = $(B License:)$(PBR $0)\n"
 "DDOC_RETURNS     = $(B Returns:)$(PBR $0)\n"
 "DDOC_SEE_ALSO    = $(B See Also:)$(PBR $0)\n"
 "DDOC_STANDARDS   = $(B Standards:)$(PBR $0)\n"
 "DDOC_THROWS      = $(B Throws:)$(PBR $0)\n"
 "DDOC_VERSION     = $(B Version:)$(PBR $0)\n"
 "DDOC_SECTION_H   = $(B $0)$(BR)\n"
 "DDOC_SECTION     = $(P $0)\n"
 "DDOC_PARAMS      = $(B Parameters:)$(PBR <table class=parms>$0</table>)\n"
 "DDOC_PARAM       = $(B $0)\n"
 "DDOC_BLANKLINE   = $(BR)\n"

 "RED    = <span style=\"color:red\">$0</span>\n"
 "GREEN  = <span style=\"color:green\">$0</span>\n"
 "BLUE   = <span style=\"color:blue\">$0</span>\n"
 "YELLOW = <span style=\"color:yellow\">$0</span>\n"
 "BLACK  = <span style=\"color:black\">$0</span>\n"
 "WHITE  = <span style=\"color:white\">$0</span>\n"
 
 "D_COMMENT = <span class=\"d_comment\">$0</span>\n"
 "D_STRING  = <span class=\"d_string\">$0</span>\n"
 "D_KEYWORD = <span class=\"d_keyword\">$0</span>\n"
 "D_PSYMBOL = <span class=\"d_psymbol\">$0</span>\n"
 "D_PARAM   = <span class=\"d_param\">$0</span>\n"
 
 "RPAREN = )\n"
 "LPAREN = (\n"
 "LESS = &lt;\n"
 "GREATER = &gt;\n"
 "D = <font face=Courier><b>$0</b></font>\n"
 "D = <span class=\"d_inlinecode\">$0</span>\n"

 "DDOC_PSYMBOL = <a name=\"$0\"></a><span class=\"ddoc_psymbol\">$0</span>\n"
 "DDOC_DECL  = <dt class=\"d_decl\">$0</dt>\n"
 "LREF = <a href=\"#$1\">$(D $1)</a>\n"
 "XREF = <a href=\"$1.html#$2\"$(D $1.$2)\n"
 "PRE = <pre>$0</pre>\n"
 
 "TABLE = <table cellspacing=0 cellpadding=5><caption>$1</caption>$2</table>\n"
 "TD = <td valign=top>$0</td>\n"
 "SUB = <sub>$0</sub>\n")

template_header =\
("\n<html lang='en'>\n"
 "<head>\n"
 "<meta http-equiv=\"content-type\" content=\"text/html; charset=utf-8\" >\n"
 "<title>$(TITLE) - $(PROJECT_NAME) $(PROJECT_VERSION) API documentation</title>\n"
 "<link rel=\"stylesheet\" type=\"text/css\" href=\"css/style.css\">\n"
 "</head>\n\n")

template_footer =\
("\n<div id=\"copyright\">\n"
 "$(COPYRIGHT) |\n"
 "Page generated by Autodoc and $(LINK2 http://www.digitalmars.com/d/2.0/ddoc.html, Ddoc).\n"
 "</div>\n\n")

default_css =\
("body\n"
 "{\n"
 "    margin: 0;\n"
 "    padding: 0;\n"
 "    border: 0;\n"
 "    color: black;\n"
 "    background-color: #1f252b;\n"
 "    font-size: 100%;\n"
 "    font-family: Verdana, \"Deja Vu\", \"Bitstream Vera Sans\", sans-serif;\n"
 "}\n"
 "\n"
 "h1, h2, h3, h4, h5, h6\n"
 "{\n"
 "    font-family: Georgia, \"Times New Roman\", Times, serif;\n"
 "    font-weight: normal;\n"
 "    color: #633;\n"
 "    line-height: normal;\n"
 "    text-align: left;\n"
 "}\n"
 "\n"
 "h1\n"
 "{\n"
 "    margin-top: 0;\n"
 "    font-size: 2.5em;\n"
 "}\n"
 "\n"
 "h2{font-size: 1.7em;}\n"
 "\n"
 "h3{font-size: 1.35em;}\n"
 "\n"
 "h4\n"
 "{\n"
 "    font-size: 1.15em;\n"
 "    font-style: italic;\n"
 "    margin-bottom: 0;\n"
 "}\n"
 "\n"
 "pre\n"
 "{\n"
 "    background: #eef;\n"
 "    padding: 1ex;\n"
 "    margin: 1em 0 1em 3em;\n"
 "    font-family: monospace;\n"
 "    font-size: 1.2em;\n"
 "    line-height: normal;\n"
 "    border: 1px solid #ccc;\n"
 "    width: auto;\n"
 "}\n"
 "\n"
 "dd\n"
 "{\n"
 "    padding: 1ex;\n"
 "    margin-left: 3em;\n"
 "    margin-bottom: 1em;\n"
 "}\n"
 "\n"
 "td{text-align: justify;}\n"
 "\n"
 "hr{margin: 2em 0;}\n"
 "\n"
 "a{color: #006;}\n"
 "\n"
 "a:visited{color: #606;}\n"
 "\n"
 "/* These are different kinds of <pre> sections */\n"
 ".console /* command line console */\n"
 "{\n"
 "    background-color: #f7f7f7;\n"
 "    color: #181818;\n"
 "}\n"
 "\n"
 ".moddeffile /* module definition file */\n"
 "{\n"
 "    background-color: #efeffe;\n"
 "    color: #010199;\n"
 "}\n"
 "\n"
 ".d_code /* D code */\n"
 "{\n"
 "    background-color: #fcfcfc;\n"
 "    color: #000066;\n"
 "}\n"
 "\n"
 ".d_code2 /* D code */\n"
 "{\n"
 "    background-color: #fcfcfc;\n"
 "    color: #000066;\n"
 "}\n"
 "\n"
 "td .d_code2\n"
 "{\n"
 "    min-width: 20em;\n"
 "    margin: 1em 0em;\n"
 "}\n"
 "\n"
 ".d_inlinecode\n"
 "{\n"
 "    font-family: monospace;\n"
 "    font-weight: bold;\n"
 "}\n"
 "\n"
 "/* Elements of D source code text */\n"
 ".d_comment{color: green;}\n"
 ".d_string {color: red;}\n"
 ".d_keyword{color: blue;}\n"
 ".d_psymbol{text-decoration: underline;}\n"
 ".d_param  {font-style: italic;}\n"
 "\n"
 "/* Focal symbol that is being documented */\n"
 ".ddoc_psymbol{color: #336600;}\n"
 "\n"
 "div#top{max-width: 85em;}\n"
 "\n"
 "div#header{padding: 0.2em 1em 0.2em 1em;}\n"
 "div.pbr\n"
 "{\n"
 "    margin: 4px 0px 8px 10px"
 "}\n"
 "\n"
 "img#logo{vertical-align: bottom;}\n"
 "\n"
 "#main-heading\n"
 "{\n"
 "    margin-left: 1em;\n"
 "    color: white;\n"
 "    font-size: 1.4em;\n"
 "    font-family: Arial, Verdana, sans-serif;\n"
 "    font-variant: small-caps;\n"
 "    text-decoration: none;\n"
 "}\n"
 "\n"
 "div#navigation\n"
 "{\n"
 "    font-size: 0.875em;\n"
 "    float: left;\n"
 "    width: 12.0em;\n"
 "    padding: 0 1.5em;\n"
 "}\n"
 "\n"
 "div.navblock\n"
 "{\n"
 "    margin-top: 0;\n"
 "    margin-bottom: 1em;\n"
 "}\n"
 "\n"
 "div#navigation .navblock h2\n"
 "{\n"
 "    font-family: Verdana, \"Deja Vu\", \"Bitstream Vera Sans\", sans-serif;\n"
 "    font-size: 1.35em;\n"
 "    color: #ccc;\n"
 "    margin: 0;\n"
 "}\n"
 "\n"
 "div#navigation .navblock ul\n"
 "{\n"
 "    list-style-type: none;\n"
 "    margin: 0;\n"
 "    padding: 0;\n"
 "}\n"
 "\n"
 "div#navigation .navblock li\n"
 "{\n"
 "    margin: 0 0 0 0.8em;\n"
 "    padding: 0;\n"
 "}\n"
 "\n"
 "#navigation .navblock a\n"
 "{\n"
 "    display: block;\n"
 "    color: #ddd;\n"
 "    text-decoration: none;\n"
 "    padding: 0.1em 0;\n"
 "    border-bottom: 1px dashed #444;\n"
 "}\n"
 "\n"
 "#navigation .navblock a:hover{color: white;}\n"
 "\n"
 "#navigation .navblock a.active\n"
 "{\n"
 "    color: white;\n"
 "    border-color: white;\n"
 "}\n"
 "\n"
 "div#content\n"
 "{\n"
 "    min-height: 440px;\n"
 "    margin-left: 15em;\n"
 "    margin-right: 1.6em;\n"
 "    padding: 1.6em;\n"
 "    padding-top: 1.3em;\n"
 "    border: 0.6em solid #cccccc;\n"
 "    background-color: #f6f6f6;\n"
 "    font-size: 0.875em;\n"
 "    line-height: 1.4em;\n"
 "}\n"
 "\n"
 "div#content li{padding-bottom: .7ex;}\n"
 "\n"
 "div#copyright\n"
 "{\n"
 "    padding: 1em 2em;\n"
 "    background-color: #303333;\n"
 "    color: #ccc;\n"
 "    font-size: 0.75em;\n"
 "    text-align: center;\n"
 "}\n"
 "\n"
 "div#copyright a{color: #ccc;}\n"
 "\n"
 ".d_inlinecode\n"
 "{\n"
 "    font-family: Consolas, \"Bitstream Vera Sans Mono\", \"Andale Mono\", \"DejaVu Sans Mono\", \"Lucida Console\", monospace;\n"
 "}\n"
 "\n"
 ".d_decl\n"
 "{\n"
 "    font-weight: bold;\n"
 "    background-color: #E4E9EF;\n"
 "    border-bottom: solid 2px #336600;\n"
 "    padding: 2px 0px 2px 2px;\n"
 "}\n")

default_cfg =\
 ("[PROJECT]\n"
  "# Name of the project. E.g. \"AutoDDoc Documentation Generator\".\n"
  "name =\n"
  "# Project version string. E.g. \"0.1 alpha\".\n"
  "version =\n"
  "# Copyright without the \"Copyright (c)\" part. E.g. \"Joe Coder 2001-2042\".\n"
  "copyright =\n"
  "# File name of the logo of the project, if any. \n"
  "# Should be a PNG image. E.g. \"logo.png\".\n"
  "logo =\n"
  "\n"
  "[OUTPUT]\n"
  "# Directory to write the documentation to.\n"
  "# If none specified, \"autoddoc\" is used.\n"
  "directory = autoddoc\n"
  "# CSS style to use. If empty, default will be generated.\n"
  "# You can create a custom style by generating default style\n"
  "# with \"autoddoc.py -s\" and modyfing it.\n"
  "style =\n"
  "# Documentation index file to use. If empty, default will be generated.\n"
  "# You can create a custom index by generating default index\n"
  "# with \"autoddoc.py -i\" and modyfing it.\n"
  "index =\n"
  "# Any extra links to add to the sidebar of the documentation.\n"
  "# Should be in the format \"LINK DESCRIPTION\", separated by commas.\n"
  "# E.g; To add links to Google and the D language site, you would use:\n"
  "# \"http://www.google.com Google, http://d-p-l.org DLang\"\n"
  "links =\n"
  "# Source files or patterns to ignore. Supports regexp syntax.\n"
  "# E.g; To ignore main.d and all source files in the test/ directory,\n"
  "# you would use: \"main.d, test/*\"\n"
  "ignore =\n"
  "\n"
  "[DDOC]\n"
  "# Command to use to generate the documentation. \n"
  "# Can be modified e.g. to use GDC or LDC.\n"
  "ddoc_command = dmd -d -c -o-\n")

class ProjectInfo:
    """Holds project-specific data"""
    def __init__(self, name, version, copyright, logo_file):
        self.name      = name
        self.version   = version
        self.copyright = copyright
        self.logo_file = logo_file

def run_cmd(cmd):
    """Run a command and return its resolt"""
    print (cmd)
    return subprocess.call(cmd, shell=True)

def module_name(source_name):
    """Get module name of a source file (currently this only depends on its path)"""
    return os.path.splitext(source_name)[0].replace("/", ".")

def scan_sources(source_dir, ignore):
    """Get a list of relative paths all source files in specified directory."""
    sources = []
    for root, dirs, files in os.walk(source_dir):
        for filename in files:
            def add_source():
                if os.path.splitext(filename)[1] not in [".d", ".dd", ".ddoc"]:
                    return
                source = os.path.join(root, filename)
                if source.startswith("./"):
                    source = source[2:]
                for exp in ignore:
                    try:
                        if(re.compile(exp.strip()).match(source)):
                            return
                    except re.error as error:
                        print("Ignore expression is not a valid regexp: ", exp,
                              "error:", error)
                        raise error
                sources.append(source);
            add_source()
    return sorted(sources, key=str.lower)

def add_template(template_path, sources, links, project):
    """Generate DDoc template file at template_path,
    connecting to sources and links, using specified project data."""
    with open(template_path, mode="w", encoding="utf-8") as a_file:
        a_file.write(template_macros)

        #Project info.
        a_file.write("PROJECT_NAME= " + project.name + "\n")
        a_file.write("PROJECT_VERSION= " + project.version + "\n")
        a_file.write("COPYRIGHT= ")
        if project.copyright is not None and project.copyright != "":
            a_file.write("Copyright &copy; " + project.copyright)
        a_file.write("\n")
         

        #DDOC macro - this is the template itself, using other macros.
        a_file.write("DDOC = <!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.01//EN\"\n"
                     "        \"http://www.w3.org/TR/html4/strict.dtd\">\n")
        a_file.write(template_header)
        a_file.write("<body>")

        #Heading and the logo, if any.
        top = ("<div id=\"top\">\n"
               "<div id=\"header\">\n")
        if project.logo_file is not None and project.logo_file != "": 
            top += ("<img id=\"logo\" alt=\"" +
                    project.name + " logo\" src=\"images/logo.png\">")
        top += ("<a id=\"main-heading\" href=\"index.html\">"
                "$(PROJECT_NAME) $(PROJECT_VERSION) API documentation</a>\n"
                "</div>\n</div>\n\n")
        a_file.write(top)

        #Menu - user specified links.
        navigation = ("<div id=\"navigation\">\n"
                      "<div class=\"navblock\">\n"
                      "<div id=\"toctop\">\n"
                      "$(UL\n")
        for link, name in links:
            navigation += "$(LI $(LINK2 " + link + ", " + name + "))\n" 
        navigation +=  ")\n</div>\n</div>\n"

        #Menu -links to the modules.
        navigation += "<div class=\"navblock\">\n$(UL\n"
        navigation += "$(LI $(LINK2 index.html, Main page))\n"
        for source in sources:
            module = module_name(source)
            link = "$(LI $(LINK2 " + module + ".html," + module + "))\n"
            navigation += link
        navigation += ")\n</div>\n</div>\n\n"

        a_file.write(navigation)

        #Main content.
        content = "<div id=\"content\">\n<h1>$(TITLE)</h1>\n$(BODY)\n</div>\n"
        a_file.write(content)

        a_file.write(template_footer)
        a_file.write("</body>\n</html>\n")

def add_logo(project, output_dir):
    """Copy the logo, if any, to images/logo.png ."""
    if(project.logo_file is None or project.logo_file == ""):
        return
    images_path = os.path.join(output_dir, "images")
    os.makedirs(images_path, exist_ok=True)
    shutil.copy(project.logo_file, os.path.join(images_path, "logo.png"))

def generate_style(filename):
    """Write default css to a file"""
    with open(filename, mode="w", encoding="utf-8") as a_file:
        a_file.write(default_css)

def add_css(css, output_dir):
    """Copy the CSS if specified, write default CSS otherwise."""
    css_path = os.path.join(output_dir, "css")
    os.makedirs(css_path, exist_ok=True)
    css_path = os.path.join(css_path, "style.css")
    if css is None or css == "":
        generate_style(css_path)
        return
    shutil.copy(css, css_path)

def generate_index(filename):
    """Write default index to a file"""
    with open(filename, mode="w", encoding="utf-8") as a_file:
        a_file.write("Ddoc\n\n")
        a_file.write("Macros:\n")
        a_file.write("    TITLE=$(PROJECT_NAME) $(PROJECT_VERSION) API documentation\n\n")

def add_index(index, output_dir):
    """Copy the index if specified, write default index otherwise."""
    index_path = os.path.join(output_dir, "index.dd")
    if index is None or index == "":
        generate_index(index_path)
        return
    shutil.copy(index, index_path)

def generate_ddoc(sources, output_dir, ddoc_template, ddoc_command):
    """Generate documentation from sources, writing it to output_dir."""

    #Generate index html with ddoc.
    index_ddoc = os.path.join(output_dir, "index.dd")
    index_html = os.path.join(output_dir, "index.html")
    run_cmd(ddoc_command + " -Df" + index_html + " " + index_ddoc)
    os.remove(index_ddoc)

    #Now generate html for the sources.
    for source in sources:
        out_path = os.path.join(output_dir, module_name(source)) + ".html"
        run_cmd(ddoc_command + " -Df" + out_path + " " + source)

def generate_config(filename):
    """Generate default AutoDDoc config file."""
    with open(filename, mode="w", encoding="utf-8") as a_file:
        a_file.write(default_cfg)

def init_parser():
    """Initialize and return the command line parser."""
    autoddoc_description =\
        ("AutoDDoc 0.1\n"
         "Documentation generator script for D using DDoc.\n"
         "Copyright Ferdinand Majerech 2011.\n\n"
         "AutoDDoc scans subdirectories of the current directory for D or DDoc\n"
         "sources (.d, .dd or .ddoc) and generates documentation using settings\n"
         "from a configuration file.\n"
         "NOTE: AutoDDoc will only work if package/module hierarchy matches the\n"
         "directory hierarchy, so e.g. module 'pkg.util' would be in file './pkg/util.d' .")

    autoddoc_epilog =\
        ("\nTutorial:\n"
         "1. Copy the script to your project directory and move into that directory.\n" 
         "   Relative to this directory, module names must match their filenames,\n"
         "   so e.g. module 'pkg.util' would be in file './pkg/util.d' .\n"
         "2. Generate AutoDDoc configuation file. To do this, type\n"
         "   './autoddoc.py -g'. This will generate file 'autoddoc.cfg' .\n"
         "3. Edit the configuation file. Set project name, version, output\n"
         "   directory and other parameters.\n"
         "4. Generate the documentation by typing './autoddoc.py' .\n")

    parser = argparse.ArgumentParser(description= autoddoc_description,
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog = autoddoc_epilog, add_help=True)

    parser.add_argument("config_file", nargs="?", default="autoddoc.cfg",
                        help="Configuration file to use to generate documentation. "
                             "Can not be used with any optional arguments. "
                             "If not specified, 'autoddoc.cfg' is assumed. "
                             "Examples: 'autoddoc.py config.cfg' "
                             "will generate documentation using file 'config.cfg' . "
                             "'autoddoc.py' will generate documentation "
                             "using file 'autoddoc.cfg' if it exists.",
                        metavar="config_file")
    parser.add_argument("-g", "--gen-config", nargs="?", const="autoddoc.cfg",
                        help="Generate default AutoDDoc configuation file. "
                             "config_file is the filename to use. If not specified, "
                             "autoddoc.cfg is used.",
                        metavar="config_file")
    parser.add_argument("-s", "--gen-style", nargs="?", const="autoddoc_style.css",
                        help="Generate default AutoDDoc style sheet. "
                             "css_file is the filename to use. If not specified, "
                             "autoddoc_style.css is used.",
                        metavar="css_file")
    parser.add_argument("-i", "--gen-index", nargs="?", const="autoddoc_index.dd",
                        help="Generate default AutoDDoc documentation index. "
                             "index_file is the filename to use. If not specified, "
                             "autoddoc_index.dd is used.",
                        metavar="index_file")

    return parser


def main():
    parser = init_parser()
    args = parser.parse_args()

    #Generate config/style/index if requested.
    done = False;
    try:
        if args.gen_config is not None:
            generate_config(args.gen_config)
            done = True
        if args.gen_style is not None:
            generate_style(args.gen_style)
            done = True
        if args.gen_index is not None:
            generate_index(args.gen_index)
            done = True
    except IOError as error:
        print("\nERROR: Unable to generate:", error)
        return

    if done or args.config_file is None:
        return
                                        
    if not os.path.isfile(args.config_file):
        print("\nERROR: Can't find configuration file", args.config_file, "\n")
        parser.print_help()
        return

    #Load documentation config.
    config = configparser.ConfigParser()
    try: 
        config.read(args.config_file)

        project = config["PROJECT"]
        project = ProjectInfo(project["name"], 
                              project["version"], 
                              project["copyright"],
                              project["logo"])

        output = config["OUTPUT"]
        output_dir = output["directory"]
        if output_dir == "":
            output_dir = "autoddoc"
        css = output["style"]
        index = output["index"]
        links = []
        if output["links"] != "":
            for link in output["links"].split(","):
                parts = link.split(" ", 1)
                links.append((parts[0].strip(), parts[1].strip()))
        ignore = output["ignore"].split(",")
        if ignore == [""]:
            ignore = []

        ddoc_line = config["DDOC"]["ddoc_command"]
    except configparser.Error as error:
        print("Unable to parse configuration file", args.config_file, ":", error)
        return
    except IOError as error:
        print("Unable to read configuration file", args.config_file, ":", error)
        return

    #Do the actual generation work.
    try:
        #Find all .d, .dd, .ddoc files.
        sources = scan_sources(".", ignore)
        ddoc_template = os.path.join(output_dir, "AUTODDOC_TEMPLATE.ddoc")
        os.makedirs(output_dir, exist_ok=True)

        add_template(ddoc_template, sources, links, project)
        add_logo(project, output_dir)
        add_css(css, output_dir)
        add_index(index, output_dir)

        generate_ddoc(sources, output_dir, ddoc_template, ddoc_line + " " + ddoc_template);
        os.remove(ddoc_template)
    except Exception as error:
        print("Error during documentation generation:", error)


if __name__ == '__main__':
    main()
