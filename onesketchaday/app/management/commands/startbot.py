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
    telegramId = update.message.from_user['username']
    try:
        logger.info("Received image upload request from {}".format(telegramId))
        user = User.objects.get(telegramId=telegramId)
    except:
        logger.info("Denied request from {}".format(telegramId))
        update.message.reply_text("Sorry, but you are not allowed to post on this website")
        return

    try:
        logger.info("Accepted request from {}".format(telegramId))

        file = context.bot.getFile(update.message.photo[-1].file_id)
        filePath = file.file_id[:20] + ".png"

        logger.info("Downloading file ({}) from {}".format(filePath, telegramId))
        file.download(settings.MEDIA_ROOT + "/" + filePath)
        logger.info("Done downloading file ({}) from {}".format(filePath, telegramId))

        post = Post.objects.create(owner=user, image=filePath, title=update.message.caption)

        update.message.reply_text("File succesfully uploaded!")
        update.message.reply_text("Here's the link yo your new post: " + settings.SITE_URL + "post/" + post.id + "")
    except Exception as e:
        update.message.reply_text("Cannot upload requested picture: " + str(e))
    

class Command(BaseCommand):
    help = 'Updates the Participants page'

    def handle(self, *args, **options):
        updater = Updater(settings.TELEGRAM_API_TOKEN, use_context=True)
        dp = updater.dispatcher
        dp.add_handler(MessageHandler(Filters.photo, imageHandler))
        dp.add_error_handler(error)

        updater.start_polling()
        updater.idle()