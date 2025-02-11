# monitoring_app/management/commands/import_food_data.py
import csv  
from django.core.management.base import BaseCommand  
from monitoring_app.models import FoodItem  

class Command(BaseCommand):  
    help = 'Import food data from CSV file'  

    def add_arguments(self, parser):  
        parser.add_argument('csv_file', type=str, help='The CSV file containing food data')  

    def handle(self, *args, **kwargs):  
        csv_file = kwargs['csv_file']  
        try:  
            with open(csv_file, 'r') as file:  
                reader = csv.DictReader(file)  
                for row in reader:  
                    name = row['name']  
                    serving_size = float(row['serving_size'])  
                    calories = float(row['calories'])  
                    protein = float(row['protein'])  
                    fat = float(row['fat'])  
                    carbs = float(row['carbs'])  
                    FoodItem.objects.update_or_create(  
                        name=name,  
                        defaults={  
                            'serving_size': serving_size,  
                            'calories': calories,  
                            'protein': protein,  
                            'fat': fat,  
                            'carbs': carbs  
                        }  
                    )  
            self.stdout.write(self.style.SUCCESS('Food data imported successfully.'))  
        except Exception as e:  
            self.stderr.write(str(e))  