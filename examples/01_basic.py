"""
An example on how to work with the API client to get the balance of an authorized account
"""

from autolook_api import AlApiClient, Error, l
import asyncio
import dotenv
import os

# Hardcoded authorization key
# Manually starting and closing the client
# Extensive error handling
async def main_example_1():
    alacctoken = "alaccauthXXXXXXXXXXXXXXXXXXXXXXXXXX"
    alcli = AlApiClient(alacctoken)
    await alcli.start()
    try:
        balance = await alcli.get_balance()
        print(f"Balance: {balance}")
    # Catching API (client and server) specific errors
    except Error as e:
        l().error(f"Errored while trying to get balance, err: {e}")
    # Catching unexpected errors
    except Exception as e:
        l().error(f"Unexpected exception while trying to get balance, err: {e}", exc_info=True)
        # raise e
    finally:
        await alcli.close()
        
# With a .env file containing `ALACCTOKEN="alaccauthXXXXXXXXXXXXXXXXXXXXXXXXXX"`
# With an async context
# Extensive error handling
# With debug logging (prints all JSON data that the client sends and receives)
async def main_example_2():
    dotenv.load_dotenv()

    alacctoken = os.getenv("ALACCTOKEN")

    try:
        async with AlApiClient(alacctoken, debug=True) as alcli:
            balance = await alcli.get_balance()
            print(f"Balance: {balance}")
    except Error as e:
        l().error(f"Errored while trying to get balance, err: {e}", exc_info=True)
    except Exception as e:
        l().error(f"Unexpected exception while trying to get balance, err: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main_example_1())
    # asyncio.run(main_example_2())
