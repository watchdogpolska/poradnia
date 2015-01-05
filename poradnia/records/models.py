from types import NoneType
from django.db import models
from cases.models import Case


class Record(models.Model):
    case = models.ForeignKey(Case)
    created_on = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return "%s#%d" % (self.case.get_absolute_url(), self.pk)

    def get_template_list(self):
        return "%s/_%s_list.html" % (self._meta.app_label, self._meta.model_name)

    def cast(self):
        """
        This method is quite handy, it converts "self" into its correct child class. For example:

        .. code-block:: python

           class Fruit(models.Model):
               name = models.CharField()

           class Apple(Fruit):
               pass

           fruit = Fruit.objects.get(name='Granny Smith')
           apple = fruit.cast()

        :return self: A casted child class of self
        Refference: http://stackoverflow.com/a/22302235/4017156
        """
        for name in dir(self):
            try:
                attr = getattr(self, name)
                if isinstance(attr, self.__class__) and type(attr) != type(self):
                    return attr
            except:
                pass

    @classmethod
    def allPossibleRecordTypes(cls):
        #this returns a list of all the subclasses of account (i.e. accounttypeA, accounttypeB etc)
        return [str(subClass).split('.')[-1][:-2] for subClass in cls.__subclasses__()]

    def recordType(self):
        if type(self.cast()) is NoneType:
            #it is a child
            return self.__class__.__name__
        else:
            #it is a parent, i.e. an record
            return str(type(self.cast())).split('.')[-1][:-2]
    recordType.short_description = "Record type"


class Log(Record):
    text = models.TextField()
