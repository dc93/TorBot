"""
Module that contains methods for collecting all relevant data from links,
and saving data to file.
"""

import re
import httpx
import logging

from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from termcolor import cprint

from torbot.modules.linktree import LinkTree


def execute_all(
    client: httpx.Client, link: str, *, display_status: bool = False
) -> None:
    """Initialise datasets and functions to retrieve data, and execute
    each for a given link.

    Args:
        link (str): Link to be interogated.
        display_status (bool, optional): Whether to print connection
            attempts to terminal.
    """

    resp = client.get(url=link)
    validation_functions = [
        get_robots_txt,
        get_dot_git,
        get_dot_svn,
        get_intel,
        get_dot_htaccess,
        get_bitcoin_address,
    ]
    for validate_func in validation_functions:
        try:
            validate_func(client, link, resp)
        except Exception as e:
            logging.debug(e)
            cprint("Error", "red")

    soup = BeautifulSoup(resp.text, "html.parser")
    display_webpage_description(soup)


def fetch_html(
    client: httpx.Client, link: str, tree: LinkTree, save_html: bool = False
) -> None:
    resp = client.get(url=link)
    soup = BeautifulSoup(resp.text, "html.parser")

    if save_html is False:
        print(f"""
            HTML file
              {soup}
        """)
    else:  # save_html is True
        file_name = tree._get_tree_file_name()
        print(f"SAVED to {file_name}.html\n\n")
        with open(f"{file_name}.html", "w+") as f:
            f.write(str(soup))


def display_headers(response):
    """Print all headers in response object.

    Args:
        response (object): Response object.
    """
    print(
        """
          RESPONSE HEADERS
          __________________
          """
    )
    for key, val in response.headers.items():
        print("*", key, ":", val)


def get_robots_txt(
    client: httpx.Client, target: str, response: httpx.Response
) -> None:
    """Check link for Robot.txt, and if found, add link to robots dataset.

    Args:
        target (str): URL to be checked.
        response (httpx.Response): Response object containing data to check.
    """
    cprint("[*]Checking for Robots.txt", "yellow")
    base = "{0.scheme}://{0.netloc}/".format(urlsplit(target))
    client.get(base + "robots.txt")
    print(base + "robots.txt")

    matches = re.findall(r"Allow: (.*)|Disallow: (.*)", response.text)
    robots = set()
    for match in matches:
        match = "".join(match)
        if "*" not in match:
            url = base + match
            robots.add(url)
        cprint("Robots.txt found", "blue")
    if robots:
        print(robots)


def get_intel(
    client: httpx.Client, url: str, response: httpx.Response
) -> None:
    """Check link for intel, and if found, print results,
    including but not limited to website accounts and AWS buckets.

    Args:
        url (str): URL to be checked.
        response (httpx.Response): Response object containing data to check.
    """
    regex = r"""([\w\.-]+s[\w\.-]+\.amazonaws\.com)|([\w\.-]+@[\w\.-]+\.[\.\w]+)"""
    matches = re.findall(regex, response.text)
    if matches:
        print("Intel\n--------\n")
        intel = set()
        for match in matches:
            intel.add(match)
        print(intel)


def get_dot_git(
    client: httpx.Client, target: str, response: httpx.Response
) -> None:
    """Check link for .git folders exposed on public domain.

    Args:
        target (str): URL to be checked.
        response (httpx.Response): Response object containing data to check.
    """
    cprint("[*]Checking for .git folder", "yellow")
    base = "{0.scheme}://{0.netloc}/".format(urlsplit(target))
    resp = client.get(base + "/.git/config")
    if resp.status_code != 404:
        cprint("Alert!", "red")
        cprint(".git folder exposed publicly", "red")
    else:
        cprint("NO .git folder found", "blue")


def get_bitcoin_address(
    client: httpx.Client, target: str, response: httpx.Response
) -> None:
    """Check link for Bitcoin addresses, and if found, print.

    Args:
        target (str): URL to be checked.
        response (httpx.Response): Response object containing data to check.
    """
    bitcoins = re.findall(
        r"[13][a-km-zA-HJ-NP-Z1-9]{25,34}", response.text
    )
    print("BTC FOUND: ", len(bitcoins))
    for bitcoin in bitcoins:
        print("BTC: ", bitcoin)


def get_dot_svn(
    client: httpx.Client, target: str, response: httpx.Response
) -> None:
    """Check link for .svn folders exposed on public domain.

    Args:
        target (str): URL to be checked.
        response (httpx.Response): Response object containing data to check.
    """
    cprint("[*]Checking for .svn folder", "yellow")
    base = "{0.scheme}://{0.netloc}/".format(urlsplit(target))
    resp = client.get(base + "/.svn/entries")
    if resp.status_code != 404:
        cprint("Alert!", "red")
        cprint(".SVN folder exposed publicly", "red")
    else:
        cprint("NO .SVN folder found", "blue")


def get_dot_htaccess(
    client: httpx.Client, target: str, response: httpx.Response
) -> None:
    """Check link for .htaccess files on public domain.

    Args:
        target (str): URL to be checked.
        response (httpx.Response): Response object containing data to check.
    """
    cprint("[*]Checking for .htaccess", "yellow")
    base = "{0.scheme}://{0.netloc}/".format(urlsplit(target))
    resp = client.get(base + "/.htaccess")
    if resp.status_code == 403:
        cprint("403 Forbidden", "blue")
    elif resp.status_code != 404 and resp.status_code != 500:
        cprint("Alert!!", "blue")
        cprint(".htaccess file found!", "blue")
    else:
        cprint("Response", "blue")
        cprint(str(resp.status_code), "blue")


def display_webpage_description(soup: BeautifulSoup) -> None:
    """Print all meta tags found in page.

    Args:
        soup (object): Processed HTML object.
    """
    cprint("[*]Checking for meta tag", "yellow")
    metatags = soup.find_all("meta")
    for meta in metatags:
        print("Meta : ", meta)
