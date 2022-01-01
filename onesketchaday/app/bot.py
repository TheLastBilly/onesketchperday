from django.core.exceptions import *
from asgiref.sync import *
from .models import *
import logging, os

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# I hate this too, but I just need this to work by the first of jan
class PostingBot():
    def createPost(self, owner, image, title):
        return Post.objects.create(owner=owner, image=image, title=title)

    async def asyncCreatePostFromUser(self, username, title, fileName, context=None):
        logger.info('Received post request from user {}'.format(username))
        
        if len(title) > 0:
            title = title[:Post._meta.get_field('title').max_length]
        
        try:
            user = await self.getUser(username)

            if not user:
                raise ObjectDoesNotExist
        except ObjectDoesNotExist as e:
            await self.sendUserReply("Sorry, but you are not allowed to post on this website", context)
            logger.error("Rejected request from {}: {}".format(username, str(e)))
            return

        try:
            absolutePath = settings.MEDIA_ROOT + "/" + fileName
            await self.downloadImage(absolutePath, context)

            post = await sync_to_async(self.createPost)(user, fileName, title)

            await self.sendUserReply("File succesfully uploaded!", context)
            await self.sendUserReply("Here's the link yo your new post: " + settings.SITE_URL + "post/" + post.id + "", context)
        
        except Exception as e:
            logger.error("Cannot create image post for user {}: {}".format(user.username, str(e)))
            await self.sendUserReply("Cannot upload requested picture due to an internal error", context)
            if os.path.exists(absolutePath):
                os.remove(absolutePath)

    def createPostFromUser(self, username, title, fileName, context=None):
        logger.info('Received post request from user {}'.format(username))
        
        if len(title) > 0:
            title = title[:Post._meta.get_field('title').max_length]
        
        try:
            user = self.getUser(username)

            if not user:
                raise ObjectDoesNotExist
        except:
            self.sendUserReply("Sorry, but you are not allowed to post on this website", context)
            return

        try:
            absolutePath = settings.MEDIA_ROOT + "/" + fileName
            self.downloadImage(absolutePath, context)

            post = Post.objects.create(owner=user, image=fileName, title=title)

            self.sendUserReply("File succesfully uploaded!", context)
            self.sendUserReply("Here's the link yo your new post: " + settings.SITE_URL + "post/" + post.id + "", context)
        
        except Exception as e:
            logger.error("Cannot create image post for user {}: {}".format(user.username, str(e)))
            self.sendUserReply("Cannot upload requested picture due to an internal error", context)
            if os.path.exists(absolutePath):
                os.remove(absolutePath)