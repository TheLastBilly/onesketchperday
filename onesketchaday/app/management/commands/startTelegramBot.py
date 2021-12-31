from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import *
from django.core.files import File
from django.utils import timezone
from telegram.ext import *
from app.models import *
from app.utils import *
import logging, os

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def imageHandler(update, context):
    telegram_username = update.message.from_user['username']
    try:
        logger.info("Received image upload request from {}".format(telegram_username))
        user = User.objects.all().filter(telegram_username=telegram_username)[0]

        if not user:
            raise ObjectDoesNotExist
    except:
        logger.info("Denied request from {}".format(telegram_username))
        update.message.reply_text("Sorry, but you are not allowed to post on this website")
        return

    try:
        logger.info("Accepted request from {}".format(telegram_username))

        file = context.bot.getFile(update.message.photo[-1].file_id)
        filePath = file.file_id[:20] + ".png"

        logger.info("Downloading file ({}) from {}".format(filePath, telegram_username))
        file.download(settings.MEDIA_ROOT + "/" + filePath)
        logger.info("Done downloading file ({}) from {}".format(filePath, telegram_username))

        post = Post.objects.create(owner=user, image=filePath, title=update.message.caption)

        update.message.reply_text("File succesfully uploaded!")
        update.message.reply_text("Here's the link yo your new post: " + settings.SITE_URL + "post/" + post.id + "")
    except Exception as e:
        logger.info("Error downloading picture from {}: {}".format(telegram_username, str(e)))
        update.message.reply_text("Cannot upload requested picture due to an internal error")
    

class Command(BaseCommand):
    help = 'Updates the Participants page'

    def handle(self, *args, **options):
        updater = Updater(settings.TELEGRAM_API_TOKEN, use_context=True)
        dp = updater.dispatcher
        dp.add_handler(MessageHandler(Filters.photo, imageHandler))
        dp.add_error_handler(error)

        updater.start_polling()
        updater.idle()