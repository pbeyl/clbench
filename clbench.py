#
# User Cloud Experience Benchmark
#
# Copyright (c) 2021 Paul Beyleveld (pbeyleveld at netskope dot com)
#


from selenium import webdriver
from selenium.common.exceptions import TimeoutException, InvalidArgumentException, NoSuchWindowException
from webdriver_manager.chrome import ChromeDriverManager
import requests
import matplotlib.pyplot as plt
import csv
import platform
import os
import re
import shutil
import json
import certifi
from cryptography import x509


BaseDir = os.path.dirname(os.path.realpath(__file__))
config = []

if platform.system() == "Windows":
    OS = "Windows"
    clearterminal = "cls"
    profile_path = BaseDir + "\\Chrome\\Default"
    datafile = BaseDir + "\\test_results.csv"
    urllist = BaseDir + "\\urls.csv"
elif platform.system() == "Darwin":
    OS = "OS X"
    clearterminal = "clear"
    profile_path = BaseDir + "/Chrome/Default"
    datafile = BaseDir + "/test_results.csv"
    urllist = BaseDir + "/urls.csv"
else:
    print("WARNING: Linux is untested, please report bugs?")
    #quit()
    OS = "Linux"
    clearterminal = "clear"
    profile_path = BaseDir + "/Chrome/Default"
    datafile = BaseDir + "/test_results.csv"
    urllist = BaseDir + "/urls.csv"

chrome_options = webdriver.chrome.options.Options()
#chrome_options.binary_location = chromebin
chrome_options.add_argument("--user-data-dir=" + profile_path)

#chrome_options.add_argument("--auto-open-devtools-for-tabs")
#chrome_options.add_argument("--headless")


def saveconfig():
    global config
    with open('config.json', 'w') as file:
        json.dump(config, file)
        file.close()


def graph_data():
    data = []
    # Read urls from .csv file
    with open(datafile, 'r') as file:
        reader = csv.DictReader(file)

        for row in reader:
            data.append(row)
        # print(data)
        file.close()

    fields = list(data[0])
    plt.suptitle("Cloud Experience Benchmark", fontsize=16, fontweight='bold')
    plt.title("smaller load time is better/quicker")
    plt.xlabel("Sites Tested")
    plt.ylabel("Load Time (ms)")

    plt.xticks(rotation=90, fontsize=7)
    plt.subplots_adjust(bottom=0.35)

    #print(fields)

    urls = []
    for x in range(len(fields)):
        result = []
        series = fields[x]
        for row in data:
            if x == 0:
                urls.append(row[series])
            else:
                result.append(int(row[series]))
                #print(int(row[series]))

        if len(result) > 0:
            plt.plot(urls, result, label=fields[x], marker='o')


    plt.legend(loc='upper right')
    print("Close graph window to continue")
    plt.show()

# Used to remove all LF and CR characters from strings in order to compare content
def flat_string(input):
    no_cr = input.replace('\r', '')
    return no_cr.replace('\n', '')


def addcert(mycert):
    cafile = certifi.where()

    b_mycert = bytes(flat_string(mycert), 'utf-8')
    #print(b_mycert)

    with open(cafile, 'r') as castore:
        trustedcerts = castore.read()
        castore.close()

    b_trustedcerts = bytes(flat_string(trustedcerts), "utf-8")

    if b_trustedcerts.find(b_mycert) != -1:
        print('Not installed, Custom CA cert already present in Certifi store.')
    else:
        with open(cafile, 'ab') as castore:
            castore.write(bytes(mycert, 'utf-8'))
            castore.close()
            print('Successfully installed Custom CA cert to Certifi store.')

    input("\nPress <ENTER> to continue")
    return


def netskopecert():
    with open('caadmin.netskope.com.pem', 'r') as infile:
        customca = infile.read()
        infile.close()
    addcert(customca)

    return


def customcert():
    #customca = input("Paste Base64 encoded(PEM) certificate, enter on new line to continue: ")
    print("Enter/Paste your Base64 encoded(PEM) certificate. <ENTER> on blank line to save it.")

    contents = []
    while True:
        line = input()
        if line == "":
            break
        contents.append(line)

    customcert = '\r\n'.join(contents) + "\r\n"

    #customcert.strip('\r\n')
    #customcert.strip('\r\n')
    #print(bytes(customcert, 'utf-8'))
    try:
        cert = x509.load_pem_x509_certificate(bytes(customcert, 'utf-8'))
        print('Certificate: ' + str(cert.subject))
    except ValueError as val:
        print("Invalid input detected, unable to decode certificate.")
        input("\nPress <ENTER> to continue")
        return


    # Call addcert method with byte string
    addcert(customcert)

    return


def set_customcert():
    while True:

        print("\n## Import Custom Certificate ##")
        print("--------------------------------\n")
        print("1. Install Netskope Decryption Cert")
        print("2. Paste BASE64 encoded PEM on cli")
        print("5. Return to previous menu")
        try:
            choice = int(input("\nEnter a menu option: "))
        except Exception:
            choice = 99

        choices = {
            1: netskopecert,
            2: customcert,
            5: exitmenu,
        }
        act = choices.get(choice, default)()
        if act == 99:
            break

        os.system(clearterminal)

def install_cert():
    os.system(clearterminal)

    try:
        print('Checking connection to googleapis...')
        test = requests.get('https://chromedriver.storage.googleapis.com')
        print('Connection OK, custom certificate installation probably not required')
    except requests.exceptions.SSLError as err:
        print('SSL Error, it might be required to install a proxy decryption certificate.\n')

    set_customcert()

    return


def runtest():
    global config
    global datafile

    os.system(clearterminal)
    if config["test_type"] == "proxy" and config["proxy"] == "":
        input("ERR: Cannot run proxy based test, configure proxy settings first")
        return 99

    test_label = input("Input test label: ")
    while not re.match("^.+$", test_label):
        print("ERR: Invalid input [ " + test_label + " ], try again")
        test_label = input("\nInput test label: ")

    print("\n## Test Information ##")
    print("-----------------------\n")
    print("Label: " + test_label)
    print("Test Type: " + config["test_type"])
    if config["test_type"] == "proxy":
        print("Proxy: " + config["proxy"])
        chrome_options.add_argument("--proxy-server=" + config["proxy"])
    print("Incognito Mode: " + config["incognito"])
    if re.match("^y|yes$", config["incognito"], re.IGNORECASE):
        chrome_options.add_argument("--incognito")
    print("")
    choice = input("Is the settings correct, initiate test? (y/n): ")
    while not re.match("^y|yes|n|no$", choice, re.IGNORECASE):
        print("ERR: Invalid input [ " + choice + " ], try again")
        choice = input("\nIs the settings correct, initiate test? (y/n): ")

    if str.lower(choice[0]) == "n":
        os.system(clearterminal)
        return 99

    os.system(clearterminal)
    if config["clear_storage"] == "y":
        print("Clearing Chrome Profile..")
        try:
            if os.path.exists(profile_path):
                shutil.rmtree(profile_path)
                print("Successfully removed the Chrome Profile")
            else:
                print("No existing Chrome profile found")
        except Exception as ex:
            print("Failed to delete the Chrome Profile")
        # driver.execute_script('window.localStorage.clear();')

    print("Initiating test. Loading new Chrome session")
    print("NB: Do not interact with or close the script or chrome browser window until tests have been completed!\n")

    try:
        mychromedriver = ChromeDriverManager(log_level=0, cache_valid_range=7)
        mychromedriverexe = mychromedriver.install()
    except requests.exceptions.SSLError as err:
        #install_cert()
        print("Test Failed: SSL/TLS Interception detected, install the decryption certificate using ""Test Settings"" menu item")
        input("Press <ENTER> to continue...")
        return
    except Exception as e:
        print(e.__doc__)
        print(e.__context__)

        '''
        chrome_type = ChromeType.GOOGLE
        browser_version = chrome_version(chrome_type)
        driver_name = mychromedriver.driver.get_name()
        os_type = mychromedriver.driver.get_os_type()
        driver_version = mychromedriver.driver.get_version()

        mychromedriverexe = mychromedriver.driver_cache.find_driver(browser_version, driver_name, os_type,
                                                    driver_version)
                                                    '''
        print("Test Failed: Could not download the required chrome webdriver")
        input("Press <ENTER> to continue...")
        return

    #print(binary_path)
    #print(mychromedriverexe)


    try:
        test_detail = requests.get('http://ip-api.com/json', verify=False).text
        print("Test Detail: " + test_detail)
    except Exception as e:
        print(e.__doc__)
        print(e.__context__)

    data = []
    # Read urls from .csv file
    with open(datafile, 'r') as file:
        reader = csv.DictReader(file)

        for row in reader:
            data.append(row)
        # print(data)
        file.close()

    try:
        #driver = webdriver.Chrome(chromedriver, options=chrome_options)
        driver = webdriver.Chrome(mychromedriverexe, options=chrome_options)
        driver.set_page_load_timeout(20)    #Set page load timeout


        for row in data:
            summ = 0
            i = 0

            # GET link consecutively for number of passes
            while i < config["passes"]:

                i = i + 1

                try:
                    driver.get(row['url'])
                except TimeoutException as ex:
                    print("Timeout occurred requesting site, retrying pass")
                    i = i - 1

                    continue
                except InvalidArgumentException as ex:
                    print("ERR: Test failed, close any open Chrome browsers and re-run the test.")
                    #print(ex.__doc__)
                except Exception as e:
                    print(e.__doc__)

                navigationStart = driver.execute_script("return window.performance.timing.navigationStart")
                redirectStart = driver.execute_script("return window.performance.timing.redirectStart")
                redirectEnd = driver.execute_script("return window.performance.timing.redirectEnd")
                domainLookupStart = driver.execute_script("return window.performance.timing.domainLookupStart")
                domainLookupEnd = driver.execute_script("return window.performance.timing.domainLookupEnd")
                connectStart = driver.execute_script("return window.performance.timing.connectStart")
                connectEnd = driver.execute_script("return window.performance.timing.connectEnd")
                requestStart = driver.execute_script("return window.performance.timing.requestStart")
                responseStart = driver.execute_script("return window.performance.timing.responseStart")
                responseEnd = driver.execute_script("return window.performance.timing.responseEnd")
                domLoading = driver.execute_script("return window.performance.timing.domLoading")
                domComplete = driver.execute_script("return window.performance.timing.domComplete")
                loadEventStart = driver.execute_script("return window.performance.timing.loadEventStart")
                loadEventEnd = driver.execute_script("return window.performance.timing.loadEventEnd")

                redirect_calc = redirectEnd - redirectStart
                dns_calc = domainLookupEnd - domainLookupStart
                tcp_calc = connectEnd - connectStart
                request_calc = responseStart - requestStart
                response_calc = responseEnd - responseStart
                processing_calc = domComplete - domLoading
                onload_calc = loadEventEnd - loadEventStart
                frontend_calc = domComplete - responseStart
                backend_calc = responseStart - navigationStart
                total_calc = frontend_calc + backend_calc
                summ += total_calc

            # calculate average and store in results dictionary
            row[test_label] = (int)(summ / config["passes"])  # calculate the average

            print(row)

    except NoSuchWindowException as ex:
        print("ERR: Test failed, did you close the browser window?")
        input("Press <ENTER> to continue...")
        return
    except Exception as e:
        print(e.__doc__)
        print(e.__context__)
        print("ERR: Test failed.")
        input("Press <ENTER> to continue...")
        return

    driver.quit()
    # print(data)

    # writing result metrics in file
    fields = list(data[0])

    with open(datafile, 'w') as file:
        writer = csv.DictWriter(file, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(data)
        file.close()

    print("Test Completed, you can now plot the data using the graph menu option.")
    graph_data()
    #input("Press ENTER to continue...")


def loadlist():
    global datafile
    os.system(clearterminal)
    print("### WARNING ###")
    choice = input("Do you want to clear ALL test data? (yes/NO): ")
    if not choice == "yes":
        if re.match("^YES|y|Yes$", choice):
            print("Changes aborted, yes is case sensitive")
        else:
            print("Changes aborted")
        input("\nPress ENTER to continue..")
        return 99
    else:
        shutil.copyfile(urllist, datafile)
        print("Test data successfully reset.")
        input("\nPress ENTER to continue..")


def info():
    os.system(clearterminal)
    print("\n## Environment ##")
    print("-----------------\n")
    print("Operating System: " + OS)
    print("Testing Method: " + config["test_type"])
    print("Proxy: " + config["proxy"])
    print("GET Requests per Site: " + str(config["passes"]))
    print("Working Directory: " + BaseDir)
    print("Trusted CA Store: " + certifi.where())
    print("Data File: test_results.csv")

    data = []
    # Read urls from .csv file
    with open(datafile, 'r') as file:
        reader = csv.DictReader(file)

        for row in reader:
            data.append(row["url"])
        # print(data)
        file.close()
    print("Test URL List: ")
    print(data)

    input("\nPress enter key to return to menu")


def default():
    input("Invalid input, press enter to continue")


def setproxy():
    global config
    value = input("Input proxy server address and port ( <fqdn|ip>:<port> ): ")
    if not re.match("^[A-Za-z0-9\.]+:\d{2,5}$", value):
        input("ERR: Invalid input [ " + value + " ], press enter to continue")
        return
    else:
        config["proxy"] = value
        saveconfig()


def setpasses():
    global config
    try:
        value = int(input("Enter number of times each URL is requested: "))
    except Exception:
        input("ERR: Invalid input, press enter to continue")
        return
    else:
        config['passes'] = value
        saveconfig()


def setincognito():
    global config
    value = input("Would you like the browser to start in incognito mode ( y/n ): ")
    if not re.match("^y|yes|n|no$", value, re.IGNORECASE):
        input("ERR: Invalid input [ " + value + " ], press enter to continue")
        return
    else:
        config["incognito"] = value
        saveconfig()


def typedirect():
    global config
    config["test_type"] = "direct"
    saveconfig()
    return 99


def typeproxy():
    global config
    config["test_type"] = "proxy"
    saveconfig()
    return 99


def exitmenu():
    print("Return to main menu")
    return 99


def close():
    quit()


def settest():
    while True:
        os.system(clearterminal)

        print("## Set Test Type ##")
        print("---------------------\n")
        print("1. Direct")
        print("2. Proxy")
        print("5. Return to previous menu")
        try:
            choice = int(input("\nEnter a menu option: "))
        except Exception:
            choice = 99

        choices = {
            1: typedirect,
            2: typeproxy,
            5: exitmenu,
        }
        act = choices.get(choice, default)()
        if act == 99:
            break


def settings_menu():
    global config

    while True:
        os.system(clearterminal)

        print("## Testing Settings ##")
        print("------------------------\n")
        print("1. Edit test method [" + config["test_type"] + "]")
        print("2. Edit proxy settings [" + config["proxy"] + "]")
        print("3. Edit number of Requests per URL [" + str(config["passes"]) + "]")
        print("4. Edit incognito mode [" + str(config["incognito"]) + "]")
        print("5. Install Decryption Certificate")
        print("6. Display Info")
        print("7. Return to previous menu")
        try:
            choice = int(input("\nEnter a menu option: "))
        except Exception:
            choice = 99

        choices = {
            1: settest,
            2: setproxy,
            3: setpasses,
            4: setincognito,
            5: install_cert,
            6: info,
            7: exitmenu,
        }
        act = choices.get(choice, default)()
        if act == 99:
            break


def main_menu():
    os.system(clearterminal)

    print("## Page Load Timer ##")
    print("---------------------\n")
    print("1. Run Test")
    print("2. Settings")
    print("3. Clear Results")
    print("4. Display Info")
    print("5. Graph Results")
    print("6. Exit")
    try:
        choice = int(input("\nEnter a menu option: "))
    except Exception:
        choice = 99

    choices = {
        1: runtest,
        2: settings_menu,
        3: loadlist,
        4: info,
        5: graph_data,
        6: close,
    }
    choices.get(choice, default)()


def main():
    global config

    try:
        with open('config.json', 'r') as file:
            config = json.load(file)
            file.close()
    except Exception:
        print("## Warning: Could not load config.json so loading default settings")
        config = {"test_type": "direct", "proxy": "", "passes": 3, "incognito": "n", "clear_storage": "y"}
        saveconfig()

    if not os.path.isdir(profile_path):
        print("# Warning: Chrome profile not found, will create new one")

    if not os.path.isfile(datafile):
        shutil.copyfile(urllist, datafile)
        print("Testing data successfully initialized.")

    while True:
        main_menu()


if __name__ == "__main__":
    main()
