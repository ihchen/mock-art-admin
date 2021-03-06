from slugify import slugify
from PIL import Image
from flask import url_for
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, app
from config import BASE_DIR, THUMBNAIL_SIZE, THUMBNAIL_SIZE_LARGE

import os
import random
import string
import math
import sys

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    header = db.Column(db.String(255))
    description = db.Column(db.Text)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    paintings = db.relationship('Painting', backref='category', lazy='dynamic')
    thumbsize_large = db.Column(db.Boolean, default=False)

    def __init__(self, **kwargs):
        slug = slugify(kwargs.get('name'))
        slug_already_exists = Category.query.filter_by(slug=slug).count()
        if slug_already_exists:
            slug = slug + "-0"
            # If a slug that was originally used for uniqueness, increment count
            while(Category.query.filter_by(slug=slug).count()):
                num = int(slug[len(slug)-1])
                slug = slug[:-1] + str(num+1)

        kwargs['slug'] = slug
        super().__init__(**kwargs)

    def __repr__(self):
        return self.name

class Painting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    medium = db.Column(db.String(255))
    dimensions = db.Column(db.String(255))
    year = db.Column(db.String(255))
    filename = db.Column(db.String, unique=True, nullable=False)
    thumbname = db.Column(db.String, unique=True, nullable=False)
    category_name = db.Column(db.String, db.ForeignKey('category.name'))
    category_order = db.Column(db.Integer, nullable=True)

    @staticmethod
    def makeThumbnail(src, dest, large=False):
        # Unnecessariness caused by Pillows resource warning
        try:
            img_file = open(src, 'rb')
            img_file.close()
        except IOError:
            return False

        if large:
            sizeToUse = THUMBNAIL_SIZE_LARGE
        else:
            sizeToUse = THUMBNAIL_SIZE

        with open(src, 'rb') as img_file:
            with Image.open(img_file) as im:
                _,_,width,height = im.getbbox()
                crop = None

                if width < height:
                    size = ((sizeToUse/width)*height)
                    crop = (0, size/2-sizeToUse/2, sizeToUse, math.ceil(size/2+sizeToUse/2))
                elif width > height:
                    size = ((width/height)*sizeToUse)
                    crop = (size/2-sizeToUse/2, 0, math.ceil(size/2+sizeToUse/2), sizeToUse)
                else:
                    size = sizeToUse
                im.thumbnail((size, size))
                if not crop is None:
                    im = im.crop(crop)

                im.save(dest)

    def __init__(self, *args, **kwargs):
        # Autoincrement category_order field if not given
        if kwargs.get('category_order') is None:
            last = None
            category_given = True
            if kwargs.get('category'):
                last = Painting.query.filter_by(category=kwargs['category']).order_by(Painting.category_order.desc()).first()
            elif kwargs.get('category_name'):
                last = Painting.query.filter_by(category_name=kwargs['category_name']).order_by(Painting.category_order.desc()).first()
            else:
                category_given = False

            if last:
                kwargs['category_order'] = last.category_order+1
            # First painting in given category
            elif category_given:
                kwargs['category_order'] = 1
        # Unique filenames
        while Painting.query.filter_by(filename=kwargs.get('filename')).count():
            kwargs['filename'] = "%s_%s.jpg" % (
                kwargs.get('filename').split('.')[0],
                ''.join([random.choice(string.ascii_letters) for i in range(0,6)])
            )
        kwargs['thumbname'] = kwargs.get('filename').split('.')[0]+".thumbnail.jpg"

        super().__init__(**kwargs)

    def __repr__(self):
        return self.name

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    embed_url = db.Column(db.String, unique=True, nullable=False)

    def __repr__(self):
        return self.name

class About(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String)
    quote = db.Column(db.String)
    quotee = db.Column(db.String)

    def __init__(self, *args, **kwargs):
        if not kwargs.get('description'):
            kwargs['description'] = ''
        if not kwargs.get('quote'):
            kwargs['quote'] = ''
        if not kwargs.get('quotee'):
            kwargs['quotee'] = ''
        super().__init__(**kwargs)