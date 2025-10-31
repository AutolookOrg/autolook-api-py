# Autolook API Client
- The official API wrapper for Python of the https://autolook.al API.
- The API documentation can be found at https://autolook.al/api
- The Package is also uploaded to GitHub: https://github.com/AutolookOrg/autolook-api-py
- The Repo is also uploaded to PyPi: https://pypi.org/project/autolook-api

## Quickstart
First you want to install the library: (skip this step if you have locally cloned this library)
```bash
pip install autolook-api
```
Then you can use the API like this:
```python
from autolook_api import AlApiClient, Error, l
import asyncio, dotenv, os, time

async def main():
    dotenv.load_dotenv()

    alacctoken = os.getenv("ALACCTOKEN") # or hardcoded:
    # alacctoken = "alaccauthXXXXXXXXXXXXXXXXXXXXXXXXXXX"

    alcli = AlApiClient(alacctoken, debug=False)
    
    try:
        await alcli.start()
        
        # Buys a new email address
        email = await alcli.buy_email("outlook.com")
        l().info(f"Waiting till email: '{email}' receives a new mail (timeout 120 seconds)")

        # Tries to find new mails for 120 seconds (if found, it automatically unlocks them)
        time_start = time.perf_counter()
        new_mails = await alcli.get_new_mails_loop(email, timeout_secs=120, autobuy_locked=True, parse_links=True)
        l().info(f"New mails after: {time.perf_counter() - time_start} seconds, found mails: {len(new_mails)}")
        for mail in new_mails:
            l().debug("- Mail: %s", mail.__str__())
        print("---\nDone")
        
    except Error as e: # Library specific errors
        l().error(f"{e}", exc_info=True)
    except Exception as e: # Generic unhandled error handling
        l().error(f"Unexpected: {e}", exc_info=True)
    except KeyboardInterrupt as e: # Gracefully shutting down the client upon user exit (Ctrl+C)
        l().info("User signaled shutdown, exiting...")
    finally:
        await alcli.close()


if __name__ == "__main__":
    asyncio.run(main())
```
You can find more examples at the [./examples folder](examples/)

## Notes
- The [01_basic.py](examples/01_basic.py) 
- It is recommended to read through the code, especially the [alapi.py](autolook_api/alapi.py) and [error.py](autolook_api/error.py) files as they give a good idea of what possible API functions and the input and output structures are

## Contributions
Feel free to submit Issues (if the code is wrong) and Pull requests (expansions/feature implementations), however for support, please reach out on Telegram linked on the website
