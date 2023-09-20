import argparse
import asyncio
import email
import imaplib
import json
import telegram


def get_body(message):
    # If the message is multipart, return the text of the first text/plain part.
    if message.is_multipart():
        text = get_body(message.get_payload(0))
    # Otherwise return the message body.
    else:
        text = message.get_payload(None, True).decode()
    return text


async def send_message(message, config: dict):

    app = telegram.Bot(token=config["telegram"]["token"])

    subject = message['Subject']
    sender = message['From']
    date = message['Date']

    msg = f"""*Subject:* {subject}
*Sender:* {sender}
*Date:* {date}
"""

    msg = msg.replace("=", "\\=")
    msg = msg.replace("-", "\\-")
    msg = msg.replace(">", "\\>")
    msg = msg.replace("<", "\\<")
    msg = msg.replace(".", "\\.")
    msg = msg.replace("_", "\\_")
    msg = msg.replace("(", "\\(")
    msg = msg.replace(")", "\\)")
    msg = msg.replace("+", "\\+")

    try:
        await app.send_message(chat_id=config["telegram"]["chat_id"], text=msg, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)
    except Exception as e:
        await app.send_message(chat_id=config["telegram"]["chat_id"], text=f"Error: {e}")


def load_config():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='config.json')
    args = parser.parse_args()
    # Load the config.json file.
    with open(args.config) as f:
        config = json.load(f)
    # Return the config dictionary.
    return config


def main():
    config = load_config()
    # Connect to the Gmail IMAP server.
    imap = imaplib.IMAP4_SSL(config['imap']['host'], port=config['imap']['port'])
    # Log in to our Gmail account.
    imap.login(config['imap']['email'], config['imap']['password'])
    # Select the inbox mailbox.
    imap.select('inbox')
    # Search for unread messages.
    status, messages = imap.search(None, 'UNSEEN')
    # The search string will return a space-separated list of IDs.
    # We'll split this string into a list of IDs.
    messages = messages[0].split()
    # We'll only fetch the first 5 messages.
    messages = messages[:5]
    # Loop over the IDs and fetch the corresponding messages.
    for message_id in messages:
        # Fetch the message, based on its ID.
        result, message = imap.fetch(message_id, '(RFC822)')
        # Mark the message as unread.
        imap.store(message_id, '-FLAGS', '\Seen')
        # Parse the email message into a dictionary.
        message = email.message_from_bytes(message[0][1])
        # Send the message to our send_message function.
        asyncio.run(send_message(message, config))
    # Close the connection to the IMAP server.
    imap.close()
    # Log out of the Gmail account.
    imap.logout()


if __name__ == '__main__':
    main()
