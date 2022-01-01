from django.core.management.base import BaseCommand, CommandError
from telegram.ext import *
from app.models import *
from app.utils import *
from app.bot import *

def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)    

class Command(BaseCommand, PostingBot):
    help = 'Updates the Participants page'

    def getUser(self, index):
        return User.objects.filter(telegram_username=index)[0]

    def imageHandler(self, update, context):
        username = update.message.from_user['username']

        logger.info('Received post request from user {}'.format(username))
        file = context.bot.getFile(update.message.photo[-1].file_id)
        self.createPostFromUser(username, update.message.caption, file.file_id[:20] + ".png", [update, context])

    def sendUserReply(self, message, ctx):
        update = ctx[0]
        update.message.reply_text(message)
    
    def downloadImage(self, imagePath, ctx):
        update = ctx[0]
        context = ctx[1]

        file = context.bot.getFile(update.message.photo[-1].file_id)
        file.download(imagePath)

    def handle(self, *args, **options):
        self.updater = Updater(settings.TELEGRAM_API_TOKEN, use_context=True)
        dp = self.updater.dispatcher
        dp.add_handler(MessageHandler(Filters.photo, self.imageHandler))
        dp.add_error_handler(error)

        self.updater.start_polling()
        self.updater.idle()