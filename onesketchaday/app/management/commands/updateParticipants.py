from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import *
from django.utils import timezone
from app.models import *
from app.utils import *

class Command(BaseCommand):
    help = 'Updates the Participants page'

    def handle(self, *args, **options):
        try:
            users = User.objects.all()
            startDateVar = Variable.objects.get(name='StartDate')
        except Exception as e:
            raise CommandError(str(e))
            
        endDate = timezone.now()

        # Get the winners and losers from the current update
        for user in users:
            if not user.is_a_participant:
                continue
            
            startDate = startDateVar.date
            posts = Post.objects.filter(owner=user).order_by('date')

            # Iterate from the start date to the end one (one day at a time)
            user.is_competing = True
            while startDate <= endDate:
                try:
                    # Check if the user posted anything that day
                    found = 0
                    for post in posts:
                        if post.date.year == startDate.year and post.date.month == startDate.month and  post.date.day == startDate.day:
                            found += 1
                        else:
                            break
                    
                    if found < 1:
                        user.is_competing = False
                        break
                    
                except Exception as e:
                    user.is_competing = False
                    break

                startDate += datetime.timedelta(days=1)
            
            user.save()

        
        





