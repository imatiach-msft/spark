#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
.. attribute:: ImageSchema

    A singleton-like attribute of :class:`_ImageSchema` in this module.

.. autoclass:: _ImageSchema
   :members:
"""

from pyspark import SparkContext
from pyspark.sql.types import Row, _create_row, _parse_datatype_json_string
from pyspark.sql import DataFrame, SparkSession
import numpy as np


class _ImageSchema(object):
    """
    Internal class for `pyspark.ml.image.ImageSchema` attribute. Meant to be private and
    not to be instantized. Use `pyspark.ml.image.ImageSchema` attribute to access the
    APIs of this class.
    """

    def __init__(self):
        self._imageSchema = None
        self._ocvTypes = None
        self._imageFields = None
        self._undefinedImageType = None

    @property
    def imageSchema(self):
        """
        Returns the image schema.

        :rtype StructType: a DataFrame with a single column of images
               named "image" (nullable)

        .. versionadded:: 2.3.0
        """

        if self._imageSchema is None:
            ctx = SparkContext._active_spark_context
            jschema = ctx._jvm.org.apache.spark.ml.image.ImageSchema.imageSchema()
            self._imageSchema = _parse_datatype_json_string(jschema.json())
        return self._imageSchema

    @property
    def ocvTypes(self):
        """
        Returns the OpenCV type mapping supported

        :rtype dict: The OpenCV type mapping supported

        .. versionadded:: 2.3.0
        """

        if self._ocvTypes is None:
            ctx = SparkContext._active_spark_context
            self._ocvTypes = dict(ctx._jvm.org.apache.spark.ml.image.ImageSchema._ocvTypes())
        return self._ocvTypes

    @property
    def imageFields(self):
        """
        Returns field names of image columns.

        :rtype list: a list of field names.

        .. versionadded:: 2.3.0
        """

        if self._imageFields is None:
            ctx = SparkContext._active_spark_context
            self._imageFields = list(ctx._jvm.org.apache.spark.ml.image.ImageSchema.imageFields())
        return self._imageFields

    @property
    def undefinedImageType(self):
        """
        Returns the name of undefined image type for the invalid image.

        .. versionadded:: 2.3.0
        """

        if self._undefinedImageType is None:
            ctx = SparkContext._active_spark_context
            self._undefinedImageType = \
                ctx._jvm.org.apache.spark.ml.image.ImageSchema.undefinedImageType()
        return self._undefinedImageType

    def toNDArray(self, image):
        """
        Converts an image to a one-dimensional array.

        :param image: The image to be converted
        :rtype array: The image as a one-dimensional array

        .. versionadded:: 2.3.0
        """

        height = image.height
        width = image.width
        nChannels = image.nChannels
        return np.ndarray(
            shape=(height, width, nChannels),
            dtype=np.uint8,
            buffer=image.data,
            strides=(width * nChannels, nChannels, 1))

    def toImage(self, array, origin=""):
        """
        Converts a one-dimensional array to a two-dimensional image.

        :param array array: The array to convert to image
        :param str origin: Path to the image
        :rtype object: Two dimensional image

        .. versionadded:: 2.3.0
        """

        if array.ndim != 3:
            raise ValueError("Invalid array shape")
        height, width, nChannels = array.shape
        ocvTypes = ImageSchema.ocvTypes
        if nChannels == 1:
            mode = ocvTypes["CV_8UC1"]
        elif nChannels == 3:
            mode = ocvTypes["CV_8UC3"]
        elif nChannels == 4:
            mode = ocvTypes["CV_8UC4"]
        else:
            raise ValueError("Invalid number of channels")
        data = bytearray(array.astype(dtype=np.uint8).ravel())
        # Creating new Row with _create_row(), because Row(name = value, ... )
        # orders fields by name, which conflicts with expected schema order
        # when the new DataFrame is created by UDF
        return _create_row(self.imageFields,
                           [origin, height, width, nChannels, mode, data])

    def readImages(self, path, recursive=False, numPartitions=0,
                   dropImageFailures=False, sampleRatio=1.0):
        """
        Reads the directory of images from the local or remote source.

        :param str path: Path to the image directory
        :param SparkSession spark: The current spark session
        :param bool recursive: Recursive search flag
        :param int numPartitions: Number of DataFrame partitions
        :param bool dropImageFailures: Drop the files that are not valid images
        :param float sampleRatio: Fraction of the images loaded
        :rtype DataFrame: DataFrame with a single column of "images",
               see ImageSchema for details

        >>> df = ImageSchema.readImages('python/test_support/image/kittens', recursive=True)
        >>> df.count()
        4

        .. versionadded:: 2.3.0
        """

        ctx = SparkContext._active_spark_context
        spark = SparkSession(ctx)
        image_schema = ctx._jvm.org.apache.spark.ml.image.ImageSchema
        jsession = spark._jsparkSession
        jresult = image_schema.readImages(path, jsession, recursive, numPartitions,
                                          dropImageFailures, float(sampleRatio))
        return DataFrame(jresult, spark._wrapped)


ImageSchema = _ImageSchema()


# Monkey patch to disallow instantization of this class.
def _disallow_instance(_):
    raise RuntimeError("Creating instance of _ImageSchema class is disallowed.")
_ImageSchema.__init__ = _disallow_instance
