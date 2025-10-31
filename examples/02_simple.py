"""
An example of buying a new email and printing the first mail it receives
"""

from autolook_api import AlApiClient, Error, l
from autolook_api import alapi
import asyncio
import dotenv
import os
import time

async def main():
    dotenv.load_dotenv()

    alacctoken = os.getenv("ALACCTOKEN")

    alcli = AlApiClient(alacctoken)
    
    try:
        await alcli.start()

        balance = await alcli.get_balance()
        print(f"Balance:", balance)
        if balance <= 0:
            l().error("Balance is zero, can't continue!")
            return
        
        api_info = await alcli.get_api_info()
        print(f"Stock domains:", api_info.stock_domains)
        
        # emails = await alcli.get_emails()
        # email = emails[0]
        
        email = await alcli.buy_email("outlook.com")
        
        l().info(f"Waiting till email: '{email}' receives a new mail (timeout 600 seconds)")
        
        time_start = time.perf_counter()
        new_mails = await alcli.get_new_mails_loop(email, timeout_secs=600, autobuy_locked=True, parse_links=True)
        l().info(f"New mails after: {time.perf_counter() - time_start} seconds, found mails: {len(new_mails)}")
        for mail in new_mails:
            l().debug("- Mail: %s", mail.__str__())

        print("---\nDone")
        
    except Error as e:
        l().error(f"{e}", exc_info=True)
    except Exception as e:
        l().error(f"Unexpected: {e}", exc_info=True)
    except KeyboardInterrupt as e:
        l().info("User signaled shutdown, exiting...")
    finally:
        await alcli.close()


if __name__ == "__main__":
    asyncio.run(main())
