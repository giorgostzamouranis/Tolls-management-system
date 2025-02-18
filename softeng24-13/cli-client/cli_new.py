#!/usr/bin/env python3

from datetime import datetime
import argparse
import requests
import json
import csv
import sys

logged_in = False
role = ""

import socket

def get_local_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # This doesn't have to be reachable; it's used to determine the outbound IP.
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

# Use the retrieved IP in your BASE_URL
BASE_URL = f"http://{get_local_ip_address()}:9115/api"

session = requests.Session()

def list_users():
    global role
    if role !='admin':
        print("Access denied")
        return
    """
    Fetch and display the list of users.
    """
    try:
        response = requests.get(f"{BASE_URL}/admin/users")
        response.raise_for_status()

        # Safely attempt to parse the JSON response
        try:
            users = response.json()
        except ValueError:
            print("Error: Received invalid JSON response.")
            print("Response content:", response.text)  # Debugging
            return

        if isinstance(users, list) and users:
            print("Users:")
            for user in users:
                print(f"Username: {user['username']}, Role: {user['role']}")
        else:
            print("No users found.")

    except requests.RequestException as e:
        print(f"Error: {e}")


def usermod(username, password):
    global role
    if role !='admin':
        print("Access denied")
        return

    """
    Creates a new user or updates the password of an existing user.
    """
    try:
        data = {'username': username, 'password': password}
        response = requests.post(f"{BASE_URL}/admin/usermod", json=data)
        if response.status_code == 200:
            print("success")
        else:
            print(f"error: {response.text}")
    except requests.RequestException as e:
        print(f"Error: {e}")


def login(username, password):
    """
    Log in and establish a session. On success, update the CLI session
    to include the token in the header for future API calls and retrieve user role.
    """
    global logged_in, role
    try:
        # Use AUTH_BASE_URL here (without /api)
        login_url = f"{BASE_URL}/login?cli=true"
        response = session.post(login_url, data={"username": username, "password": password})
        if response.ok:
            try:
                user_data = response.json()
            except ValueError:
                print("Error: Received an invalid JSON response.")
                print("Response content:", response.text)
                logged_in = False
                return

            token = user_data.get("token")
            if token:
                # Save the token in the session headers for future calls
                session.headers.update({"X-OBSERVATORY-AUTH": token})
            # Now call the whoami endpoint to retrieve additional user info (including role)
            whoami_url = f"{BASE_URL}/auth/whoami"
            whoami_resp = session.get(whoami_url)
            if whoami_resp.ok:
                try:
                    info = whoami_resp.json()
                    role = info.get("role", "")
                except ValueError:
                    print("Error: Unable to parse whoami JSON response.")
                    role = ""
            else:
                print("Failed to retrieve user info from whoami endpoint.")
                role = ""
            logged_in = True
            print(f"Login successful!")
        else:
            print(f"Login failed: {response.status_code} - {response.text}")
            logged_in = False
    except requests.RequestException as e:
        print(f"Error during login: {e}")
        logged_in = False



def logout():
    global logged_in
    try:
        # Add ?cli=true so the server knows this is a CLI request.
        logout_url = f"{BASE_URL}/logout?cli=true"
        response = session.post(logout_url)
        if response.ok:
            logged_in = False
            print("Logout successful!")
            session.cookies.clear()
        else:
            print(f"Logout failed: {response.status_code} - {response.text}")
    except requests.RequestException as e:
        print(f"Error during logout: {e}")

def resetpasses():
    global role
    if role !='admin':
        print("Access denied")
        return
    
    response = session.post(f"{BASE_URL}/admin/resetpasses")
    if response.status_code == 200:
        print("Passes reset successfully!")
    else:
        print(f"Error: {response.status_code} - {response.text}")

def healthcheck():
    """
    Perform a system healthcheck.
    """
    global role
    if role !='admin':
        print("Access denied")
        return
    try:
        response = session.get(f"{BASE_URL}/admin/healthcheck", allow_redirects=False)
        if response.status_code == 200:
            print(json.dumps(response.json(), indent=4))
        elif response.status_code == 401:
            print("Unauthorized: Please log in to perform a healthcheck.")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except requests.RequestException as e:
        print(f"Error during healthcheck: {e}")

def resetstations():
    """
    Reset toll stations in the system using predefined CSV file.
    """
    global role
    if role !='admin':
        print("Access denied")
        return

    try:
        response = session.post(f"{BASE_URL}/admin/resetstations")
        if response.status_code == 200:
            print("Toll stations reset successfully!")
        elif response.status_code == 400:
            print(f"Bad request: {response.json().get('info', 'Unknown error')}")
        elif response.status_code == 403:
            print("Access denied: Admin privileges required.")
        elif response.status_code == 401:
            print("Unauthorized: Please log in to reset toll stations.")
        else:
            print(f"Unexpected error: {response.status_code} - {response.text}")
    except requests.RequestException as e:
        print(f"Error during resetstations: {e}")

def passescost(station_op, tag_op, date_from, date_to, output_format="json"):
    """
    Fetch passes cost between station operator and tag operator.
    """
    # Convert dates to the required format (YYYY-MM-DD)
    try:
        formatted_date_from = datetime.strptime(date_from, "%Y%m%d").strftime("%Y-%m-%d")
        formatted_date_to = datetime.strptime(date_to, "%Y%m%d").strftime("%Y-%m-%d")
    except ValueError:
        print("Error: Invalid date format. Use YYYYMMDD.")
        return

    url = f"{BASE_URL}/passesCost/{station_op}/{tag_op}/{formatted_date_from}/{formatted_date_to}"
    try:
        response = session.get(url)
        response.raise_for_status()
        data = response.json()

        if output_format == "json":
            # Output as JSON
            print(json.dumps(data, indent=4))
        elif output_format == "csv":
            # Output as CSV
            if "nPasses" in data and "passesCost" in data:
                keys = ["stationOp", "tagOp", "periodFrom", "periodTo", "nPasses", "passesCost"]
                output = {
                    "stationOp": station_op,
                    "tagOp": tag_op,
                    "periodFrom": formatted_date_from,
                    "periodTo": formatted_date_to,
                    "nPasses": data.get("nPasses", 0),
                    "passesCost": data.get("passesCost", 0.0),
                }
                writer = csv.DictWriter(sys.stdout, fieldnames=keys)
                writer.writeheader()
                writer.writerow(output)
            else:
                print("Unexpected response structure or no data available.")
        else:
            print(f"Unsupported format: {output_format}")
    except requests.RequestException as e:
        print(f"Error: {e}")


def charges_by(toll_op_id, date_from, date_to, output_format):
    """
    Fetch charges by visiting operators for a specific toll operator and date range.
    """
    # Convert dates to the required format (YYYY-MM-DD)
    try:
        formatted_date_from = datetime.strptime(date_from, "%Y%m%d").strftime("%Y-%m-%d")
        formatted_date_to = datetime.strptime(date_to, "%Y%m%d").strftime("%Y-%m-%d")
    except ValueError:
        print("Error: Invalid date format. Use YYYYMMDD.")
        return

    url = f"{BASE_URL}/chargesBy/{toll_op_id}/{formatted_date_from}/{formatted_date_to}"
    try:
        response = session.get(url)
        response.raise_for_status()
        data = response.json()

        if output_format == "json":
            # Output as JSON
            print(json.dumps(data, indent=4))
        elif output_format == "csv":
            # Output as CSV
            if "vOpList" in data and len(data["vOpList"]) > 0:
                keys = data["vOpList"][0].keys()
                writer = csv.DictWriter(sys.stdout, fieldnames=keys)
                writer.writeheader()
                writer.writerows(data["vOpList"])
            else:
                print("No data available for the given input.")
        else:
            print(f"Unsupported format: {output_format}")
    except requests.RequestException as e:
        print(f"Error: {e}")


def tollstationpasses(station, date_from, date_to, output_format):
    """
    Fetch toll station passes from the API and output in the specified format.
    """
    
    try:
        formatted_date_from = datetime.strptime(date_from, "%Y%m%d").strftime("%Y-%m-%d")
        formatted_date_to = datetime.strptime(date_to, "%Y%m%d").strftime("%Y-%m-%d")
    except ValueError:
        print("Error: Invalid date format. Use YYYYMMDD.")
        return

    url = f"{BASE_URL}/tollStationPasses/{station}/{formatted_date_from}/{formatted_date_to}"
    try:
        response = session.get(url)
        if response.status_code == 200:
            data = response.json()
            if output_format == "json":
                print(json.dumps(data, indent=4))
            elif output_format == "csv":
                if "passList" in data:
                    keys = data["passList"][0].keys()
                    writer = csv.DictWriter(sys.stdout, fieldnames=keys)
                    writer.writeheader()
                    writer.writerows(data["passList"])
                else:
                    print("No data available for the given input.")
            else:
                print(f"Unsupported format: {output_format}")
        elif response.status_code == 401:
            print("Unauthorized: Please log in to access this resource.")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except requests.RequestException as e:
        print(f"Error: {e}")

def passanalysis(station_op, tag_op, date_from, date_to, output_format):
    # Convert dates to the required format (YYYY-MM-DD)
    try:
        formatted_date_from = datetime.strptime(date_from, "%Y%m%d").strftime("%Y-%m-%d")
        formatted_date_to = datetime.strptime(date_to, "%Y%m%d").strftime("%Y-%m-%d")
    except ValueError:
        print("Error: Invalid date format. Use YYYYMMDD.")
        return

    url = f"{BASE_URL}/passAnalysis/{station_op}/{tag_op}/{formatted_date_from}/{formatted_date_to}"
    try:
        response = session.get(url)
        response.raise_for_status()
        data = response.json()

        if output_format == "json":
            print(json.dumps(data, indent=4))
        elif output_format == "csv":
            # Check if 'passList' exists and has at least one element
            if "passList" in data and data["passList"]:
                keys = data["passList"][0].keys()
                writer = csv.DictWriter(sys.stdout, fieldnames=keys)
                writer.writeheader()
                writer.writerows(data["passList"])
            else:
                print("No pass data available.")
        else:
            print(f"Unsupported format: {output_format}")
    except requests.RequestException as e:
        print(f"Error: {e}")

def addpasses(file_path):
    global role
    if role !='admin':
        print("Access denied")
        return
    try:
        with open(file_path, 'rb') as file:
            response = requests.post(
                f"{BASE_URL}/admin/addpasses",
                files={'file': file}
            )
            if response.status_code == 200:
                print("Passes added successfully!")
            else:
                print(f"Error: {response.status_code} - {response.text}")
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found. Please check the file path.")
    except requests.RequestException as e:
        print(f"Error: {e}")

def run_script(script_file):
    """
    Read commands from the script file, execute them one by one,
    and pause after each command until the user presses any key.
    """
    try:
        with open(script_file, 'r') as f:
            for line in f:
                # Remove any leading/trailing whitespace and skip empty lines.
                command = line.strip()
                if not command:
                    continue
                print("\n======================================")
                print(f"Executing command: {command}")
                print("======================================\n")
                parse_and_execute(command)
                # Wait for the user to press any key.
                input("Press any key to continue...")
    except FileNotFoundError:
        print(f"Error: File '{script_file}' not found.")
    except Exception as e:
        print(f"An error occurred while reading the script file: {e}")


def parse_and_execute(command):
    """
    Parse and execute commands.
    """
    global logged_in
    try:
        parts = command.split()
        if len(parts) < 2 or parts[0] != "se2413":
            print("Invalid command format. Commands must start with 'se2413'.")
            return

        scope = parts[1]
        args = parts[2:]

        # Require login for all commands except 'login'
        if scope != "login" and not logged_in:
            print("You must log in first using the 'login' command.")
            return

        # Argument parsing logic
        parser = argparse.ArgumentParser(prog="se2413", add_help=False)
        subparsers = parser.add_subparsers(dest="scope")

        login_parser = subparsers.add_parser("login", help="Log in to the system.")
        login_parser.add_argument("--username", required=True, help="Username for login.")
        login_parser.add_argument("--passw", required=True, help="Password for login.")

        logout_parser = subparsers.add_parser("logout", help="Log out of the system.")

        admin_parser = subparsers.add_parser("admin", help="Administrative commands")
        admin_parser.add_argument("--source", help="Path to the CSV file.")
        admin_parser.add_argument("--usermod", action="store_true", help="Create a new user or update password.")
        admin_parser.add_argument("--username", help="Username (required with --usermod).")
        admin_parser.add_argument("--passw", help="New password (required with --usermod).")
        admin_parser.add_argument("--users", action="store_true", help="List all users.")
        admin_parser.add_argument("--addpasses", action="store_true", help="Add passes from a CSV file.")

        healthcheck_parser = subparsers.add_parser("healthcheck", help="Perform a healthcheck.")

        resetpasses_parser = subparsers.add_parser("resetpasses", help="Reset all the passes.")

        resetstations_parser = subparsers.add_parser("resetstations", help="Reset toll stations.")

        passanalysis_parser = subparsers.add_parser("passanalysis", help="Perform pass analysis between operators.")
        passanalysis_parser.add_argument("--stationop", required=True, help="Station Operator ID")
        passanalysis_parser.add_argument("--tagop", required=True, help="Tag Operator ID")
        passanalysis_parser.add_argument("--from", required=True, dest="date_from", help="Start date (YYYYMMDD)")
        passanalysis_parser.add_argument("--to", required=True, dest="date_to", help="End date (YYYYMMDD)")
        passanalysis_parser.add_argument("--format", choices=["json", "csv"], default="csv", help="Output format (default: csv).")

        tollstation_parser = subparsers.add_parser("tollstationpasses", help="Get toll station passes.")
        tollstation_parser.add_argument("--station", required=True, help="Station ID.")
        tollstation_parser.add_argument("--from", required=True, dest="date_from", help="Start date (YYYYMMDD).")
        tollstation_parser.add_argument("--to", required=True, dest="date_to", help="End date (YYYYMMDD).")
        tollstation_parser.add_argument("--format", choices=["json", "csv"], default="csv", help="Output format (default: csv).")


        # Passes Cost scope
        passescost_parser = subparsers.add_parser("passescost", help="Fetch passes cost between operators.")
        passescost_parser.add_argument("--stationop", required=True, help="Station Operator ID")
        passescost_parser.add_argument("--tagop", required=True, help="Tag Operator ID")
        passescost_parser.add_argument("--from", required=True, dest="date_from", help="Start date (YYYYMMDD)")
        passescost_parser.add_argument("--to", required=True, dest="date_to", help="End date (YYYYMMDD)")
        passescost_parser.add_argument("--format", choices=["json", "csv"], default="csv", help="Output format (default: csv).")

        chargesby_parser = subparsers.add_parser("chargesby", help="Get charges by visiting operators.")
        chargesby_parser.add_argument("--opid", required=True, help="Toll Operator ID")
        chargesby_parser.add_argument("--from", required=True, dest="date_from", help="Start date (YYYYMMDD)")
        chargesby_parser.add_argument("--to", required=True, dest="date_to", help="End date (YYYYMMDD)")
        chargesby_parser.add_argument("--format", choices=["json", "csv"], default="csv", help="Output format (default: csv).")

        parsed_args = parser.parse_args([scope] + args)

        if parsed_args.scope == "login":
            login(parsed_args.username, parsed_args.passw)
        elif parsed_args.scope == "logout":
            logout()
        elif parsed_args.scope == "admin":
            if parsed_args.usermod:
                if not parsed_args.username or not parsed_args.passw:
                    print("Error: --username and --passw are required with --usermod.")
                else:
                    usermod(parsed_args.username, parsed_args.passw)
            elif parsed_args.users:
                list_users()
            elif parsed_args.addpasses:
                if parsed_args.source:
                    addpasses(parsed_args.source)
                else:
                    print("Error: --source argument is required with --addpasses.")
            elif parsed_args.source:
                addpasses(parsed_args.source)
        elif parsed_args.scope == "healthcheck":
            healthcheck()
        elif parsed_args.scope == "resetpasses":
            resetpasses()
        elif parsed_args.scope == "tollstationpasses":
            tollstationpasses(parsed_args.station, parsed_args.date_from, parsed_args.date_to, parsed_args.format)
        elif parsed_args.scope == "resetstations":
            resetstations()
        elif parsed_args.scope == "passanalysis":
            passanalysis(parsed_args.stationop, parsed_args.tagop, parsed_args.date_from, parsed_args.date_to, parsed_args.format)
        elif parsed_args.scope == "passescost":
            passescost(parsed_args.stationop, parsed_args.tagop, parsed_args.date_from, parsed_args.date_to, parsed_args.format)
        elif parsed_args.scope == "chargesby":
            charges_by(parsed_args.opid, parsed_args.date_from, parsed_args.date_to, parsed_args.format)
        else:
            print(f"Unknown scope: {parsed_args.scope}")
    except SystemExit:
        print("Invalid command or arguments.")

def main():
    print("Welcome to the Toll Management CLI. Type 'exit' to quit.")
    while True:
        try:
            command = input("se2413> ").strip()
            if command.lower() == "exit":
                print("Exiting CLI. Goodbye!")
                break
            parse_and_execute(command)
        except KeyboardInterrupt:
            print("\nExiting CLI. Goodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        # Check if the first argument is '--script'
        if sys.argv[1] == "--script":
            if len(sys.argv) != 3:
                print("Usage: cli_new.py --script <script_file>")
                sys.exit(1)
            script_file = sys.argv[2]
            run_script(script_file)
        else:
            # If arguments are given in a single line, join and execute.
            command = " ".join(sys.argv[1:])
            parse_and_execute(command)
    else:
        main()
