from django.db import models
from pymorphy2 import MorphAnalyzer


# Create your models here.

RU_ALPHABET = {'ё', 'е', 'о', 'ь', 'п', 'м', 'ъ', 'ч', 'щ', 'ы', 'ц', 'х', 'р', 'ж', 'ф', 'в', 'с', 'ш', 'д', 'т', 'я',
               'л', 'й', 'а', 'г', 'э', 'и', 'н', ' ', 'к', 'з', 'у','б','ю'}
morph = MorphAnalyzer()


class Category(models.Model):
    category=models.CharField(max_length=20)
    product=models.CharField(max_length=20)

class Other(models.Model):
    word=models.CharField(max_length=64)

class Product(models.Model):
    category = models.CharField(max_length=20)
    name = models.CharField(max_length=64)
    id = models.IntegerField(primary_key=True)
    urgent = models.BooleanField()

    def __init__(self, category=None, urgent=None, *args, **kwargs):
        for required_param in ('id','name'):
            if required_param not in kwargs:
                raise TypeError(f"Expected {required_param} arg")

        super().__init__(*args, **kwargs)
        if kwargs.get('urgent') is None:
            if 'срочно' in kwargs.get('name').lower():
                self.urgent = True
                self.name = kwargs.get('name').lower().replace('срочно', '').capitalize()
                while "  " in self.name:
                    self.name = self.name.replace('  ', ' ')
            else:
                self.name = kwargs.get('name')
        else:
            self.urgent = kwargs.get('urgent')
            self.name = kwargs.get('name')
        self.id = kwargs.get('id')
        if kwargs.get('category') is None:
            name_cpy = ''.join(c for c in kwargs.get('name').lower() if c in RU_ALPHABET)
            name_inf = set()
            for word in name_cpy.split(' '):
                name_inf.add(morph.parse(word)[0].normal_form)
            #print(name_inf)
            for word in name_inf:
                cat = Category.objects.filter(product=word)
                if len(cat):
                    break

            if len(cat):
                cat = 'Другое'
                Other(name=self.name).save()
            else:
                self.category = self.category[0].category

        else:
            self.category = category

    def assign_category(self):
        name_cpy = ''.join(c for c in self.name if c in RU_ALPHABET)
        name_inf = set()
        for word in name_cpy.split(' '):
            name_inf.add(morph.parse(word)[0].normal_form)
        # print(name_inf)
        for word in name_inf:
            cat = Category.objects.filter(product=word)
            if len(cat):
                break

        if len(cat):
            cat = 'Другое'
            Other(name=self.name).save()
        else:
            self.category = self.category[0].category

    # def change_name(self, new_name):
    #     self.__name = new_name
    #     try:
    #         new_name = ''.join(
    #             morph.parse(i)[0].normal_form if new_name.isalpha() else str(i) + ' ' for i in new_name.split(' '))
    #     except ValueError:
    #         new_name = self.__name
    #     found = False
    #     for word in new_name.split():
    #         if found:
    #             break
    #         else:
    #             ans = db.read_table('category_product', column_name='product', value=word.lower())
    #             if len(ans) > 0:
    #                 found = True
    #                 self.__category = ans[0][0]
    #                 break
    #     if not found:
    #         self.__category = 'Другое'
    #         try:
    #             db.add_record('Other', self.__name)
    #         except Exception:
    #             pass

    def get_button(self):
        if self.urgent:
            text = '✅❗️' + bool(len(self.name) > 27) * (self.name[:27] + '...') + bool(
                len(self.name) <= 27) * self.name + '❗️'
            # print(text)
        else:
            text = '✅' + bool(len(self.name) > 31) * (self.name[:24] + '...') + bool(
                len(self.name) <= 31) * self.name
        reply_markup = f'p&{self.id}'
        return (text, reply_markup)

    @staticmethod
    def form_family_dict(family_name: str):
        lst = Product.objects.filter(family=family_name)
        # print(lst)
        if lst is None:
            return {}
        cat_prod_dict = {}
        categories = []
        for line in lst:
            if line['fields']['category'] not in categories:
                categories.append(line['fields']['category'])
        categories.sort()
        if 'Другое' in categories:
            if categories.index('Другое') != len(categories) - 1:
                categories[categories.index('Другое')], categories[-1] = categories[-1], categories[
                    categories.index('Другое')]
        for category in categories:
            cat_prod_dict[category] = []
            for line in lst:
                if line['fields']['category'] == category:
                    cat_prod_dict[line['fields']['category']].append(Product(line['fields']['id'],
                                                                             line['fields']['product'],
                                                                             line['fields']['category'],
                                                                             True if line['fields'][
                                                                                         'urgent'] == 'True' else False))
        return cat_prod_dict

    @staticmethod
    def form_message_text(c_p_dict):
        # print('got 2 f_m_t')
        if len(c_p_dict) != 0:
            message = 'Список покупок:\n\n'
            for category in c_p_dict.keys():
                cnt = 1
                message += category + ':\n'
                for product in c_p_dict[category]:
                    try:
                        message += str(cnt) + ') ' + product.__name + '\n'
                    except TypeError:
                        pass
                    cnt += 1
        else:
            message = 'Список пуст'
        return message

    def is_urgent(self) -> bool:
        return self.urgent