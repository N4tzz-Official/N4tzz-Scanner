import requests
import re
import argparse
import json
import signal
import sys
import os
import colorama
from colorama import Fore, Style
from bs4 import BeautifulSoup

colorama.init(autoreset=True)

logo = """
    )                                                       
 ( /(     )    )                                            
 )\()) ( /( ( /(                    )               (  (    
((_)\  )\()))\()|  (      (   (  ( /(  (     (     ))\ )(   
 _((_)((_)\(_))/)\ )\     )\  )\ )(_)) )\ )  )\ ) /((_|()\  
| \| | | (_) |_((_|(_)   ((_)((_|(_)_ _(_/( _(_/((_))  ((_) 
| .` |_  _||  _|_ /_ /   (_-< _|/ _` | ' \)) ' \)) -_)| '_| 
|_|\_| |_|  \__/__/__|___/__|__|\__,_|_||_||_||_|\___||_|   
                    |_____|                                 
✔ By : N4tzzSquad (https://github.com/N4tzz-Official)
✔ Email: N4tzzOfficial@proton.me / n4tzzofficial@gmail.com
✔ © Copyright 2024 N4tzzSquadCommunity
"""

print(Fore.MAGENTA + logo)

def extract_links_from_js(js_content):
    url_pattern = r'(https?://[^\s\'"<>]+)'
    return re.findall(url_pattern, js_content)

def extract_secrets(js_content):
    secret_patterns = {
        'AWS Access Key': r'(?i)AWS_Access_Key\s*:\s*[\'"]?([A-Z0-9]{20})[\'"]?',
        'AWS Secret Key': r'(?i)AWS_Secret_Key\s*:\s*[\'"]?([A-Za-z0-9/+=]{40})[\'"]?',
        'Stripe Secret Key': r'(?i)Stripe_Secret_Key\s*:\s*[\'"]?([A-Za-z0-9]{24})[\'"]?',
        'GitHub Token': r'(?i)GitHub Token\s*:\s*[\'"]?([A-Za-z0-9]{36})[\'"]?',
        'Facebook Token': r'(?i)Facebook_Token\s*:\s*[\'"]?([A-Za-z0-9\.]+)[\'"]?',
        'Telegram Bot Token': r'(?i)Telegram Bot Token\s*:\s*[\'"]?([A-Za-z0-9:]+)[\'"]?',
        'Google Maps API Key': r'(?i)Google Maps API Key\s*:\s*[\'"]?([A-Za-z0-9_-]+)[\'"]?',
        'Google reCAPTCHA Key': r'(?i)Google reCAPTCHA Key\s*:\s*[\'"]?([A-Za-z0-9_-]+)[\'"]?',
        'API Key': r'(?i)API_Key\s*:\s*[\'"]?([A-Za-z0-9_-]{32,})[\'"]?',
        'Secret Key': r'(?i)Secret_Key\s*:\s*[\'"]?([A-Za-z0-9_-]{32,})[\'"]?',
        'Auth Domain': r'(?i)Auth_Domain\s*:\s*[\'"]?([A-Za-z0-9\-]+\.[a-z]{2,})[\'"]?',
        'Database URL': r'(?i)Database_URL\s*:\s*[\'"]?([^\'" ]+)[\'"]?',
        'Storage Bucket': r'(?i)Storage_Bucket\s*:\s*[\'"]?([^\'" ]+)[\'"]?',
        'Cloud Storage API Key': r'(?i)Cloud Storage API Key\s*:\s*[\'"]?([A-Za-z0-9_-]{32,})[\'"]?'
    }

    found_secrets = {}
    for key, pattern in secret_patterns.items():
        matches = re.findall(pattern, js_content)
        if matches:
            found_secrets[key] = list(set(matches))

    object_pattern = r'(?i)const\s+[A-Z_]+_KEYS\s*=\s*\{([^}]+)\}'
    object_matches = re.findall(object_pattern, js_content)
    
    for match in object_matches:
        for line in match.split(','):
            line = line.strip()
            for key in secret_patterns.keys():
                if key.lower().replace(' ', '_') in line.lower():
                    value = re.search(r'\:\s*[\'"]?([^\'", ]+)[\'"]?', line)
                    if value:
                        found_secrets.setdefault(key, []).append(value.group(1))

    return found_secrets

def signal_handler(sig, frame):
    choice = input(f"{Fore.YELLOW}[INFO]{Style.RESET_ALL} Do you want to close? (Y/N): ").strip().lower()
    if choice == 'y':
        print(f"{Fore.GREEN}[INFO]{Style.RESET_ALL} Closing...")
        sys.exit(0)
    else:
        print(f"{Fore.GREEN}[INFO]{Style.RESET_ALL} Continuing execution...")

def main(input_file, output_file, look_for_secrets, look_for_urls, single_url):
    os.system('cls' if os.name == 'nt' else 'clear')
    print(logo)

    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

    js_links = []
    if single_url:
        js_links.append(single_url)
    else:
        if not os.path.isfile(input_file):
            print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Input file does not exist.")
            sys.exit(1)
        with open(input_file, 'r') as file:
            js_links = file.readlines()

    extracted_links = []
    all_secrets = {}

    for js_link in js_links:
        js_link = js_link.strip()
        if not js_link:
            continue
        
        try:
            response = requests.get(js_link, verify=False)
            response.raise_for_status()

            if look_for_urls:
                links = extract_links_from_js(response.text)
                extracted_links.extend(links)
                print(f"{Fore.BLUE}[INFO]{Style.RESET_ALL} {Fore.YELLOW}Extracted {len(links)} links from {js_link}{Style.RESET_ALL}")

                for link in links:
                    print(f"{Fore.GREEN}[+] {link}{Style.RESET_ALL}")
                if not links:
                    print(f"{Fore.RED}[INFO]{Style.RESET_ALL} {Fore.YELLOW}No URLs found in {js_link}{Style.RESET_ALL}")

            if look_for_secrets:
                secrets = extract_secrets(response.text)
                if secrets:
                    all_secrets[js_link] = secrets
                    print(f"{Fore.GREEN}[+] Secrets found in {js_link}: {json.dumps(secrets, indent=2)}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}[INFO]{Style.RESET_ALL} {Fore.YELLOW}No secrets found in {js_link}{Style.RESET_ALL}")

        except requests.exceptions.SSLError as ssl_err:
            print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} SSL error while fetching {js_link}: {str(ssl_err)}")
        except requests.RequestException as e:
            print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Failed to fetch {js_link}: {str(e)}")

    if extracted_links and look_for_urls:
        with open(output_file, 'w') as out_file:
            for link in extracted_links:
                out_file.write(link + '\n')
        print(f"{Fore.BLUE}[INFO]{Style.RESET_ALL} {Fore.YELLOW}Links saved to {output_file}{Style.RESET_ALL}")

    if all_secrets and look_for_secrets:
        secrets_output_file = output_file.replace('.txt', '_secrets.json')
        with open(secrets_output_file, 'w') as secrets_file:
            json.dump(all_secrets, secrets_file, indent=2)
        print(f"{Fore.BLUE}[INFO]{Style.RESET_ALL} {Fore.YELLOW}Secrets saved to {secrets_output_file}{Style.RESET_ALL}")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTSTP, signal_handler)

    parser = argparse.ArgumentParser(description='Extract links and secrets from JavaScript files.')
    parser.add_argument('input_file', nargs='?', help='File containing JavaScript links')
    parser.add_argument('-o', '--output_file', default='extracted_links.txt', help='File to save extracted links')
    parser.add_argument('-u', '--url', help='Single JavaScript URL to fetch')
    parser.add_argument('--secrets', action='store_true', help='Look for secrets in JavaScript content')
    parser.add_argument('--urls', action='store_true', help='Extract URLs from JavaScript content')
    args = parser.parse_args()

    if not args.input_file and not args.url:
        print(f"{Fore.BLUE}[INFO]{Style.RESET_ALL} {Fore.YELLOW} Please provide either an input file or a single URL.{Style.RESET_ALL}")
        sys.exit(1)
    if args.url and args.input_file:
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} Please provide either an input file or a single URL, not both.")
        sys.exit(1)

    main(args.input_file, args.output_file, args.secrets, args.urls, args.url)
