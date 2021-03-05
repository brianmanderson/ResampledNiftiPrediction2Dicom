__author__ = 'Brian M Anderson'
# Created on 3/5/2021
import numpy as np
import SimpleITK as sitk
import os, time
from Dicom_RT_and_Images_to_Mask.src.DicomRTTool import DicomReaderWriter, plot_scroll_Image


path = r'R:\Team Share\Kareem Wahid\Pilot_T2_study\Brian'
out_path = r'R:\Team Share\Kareem Wahid\Pilot_T2_study\Brian\New_Dicom'
reader = DicomReaderWriter()

reader.walk_through_folders(input_path=path)
for root, folder, files in os.walk(path):
    nii_files = [i for i in files if i.endswith('.nii.gz')]
    if nii_files:
        resampled_image = sitk.ReadImage(os.path.join(root, 'T2.nii.gz'))
        prediction = sitk.ReadImage(os.path.join(root, 'T2_gtvp.nii.gz'))
        xxx = 1

reader.get_images()
series_reader = reader.reader

# Configure the reader to load all of the DICOM tags (public+private):
# By default tags are not loaded (saves time).
# By default if tags are loaded, the private tags are not loaded.
# We explicitly configure the reader to load tags, including the
# private ones.
series_reader.MetaDataDictionaryArrayUpdateOn()
series_reader.LoadPrivateTagsOn()
image3D = reader.dicom_handle


# Write the 3D image as a series
# IMPORTANT: There are many DICOM tags that need to be updated when you modify an
#            original image. This is a delicate opration and requires knowlege of
#            the DICOM standard. This example only modifies some. For a more complete
#            list of tags that need to be modified see:
#                           http://gdcm.sourceforge.net/wiki/index.php/Writing_DICOM

writer = sitk.ImageFileWriter()
# Use the study/series/frame of reference information given in the meta-data
# dictionary and not the automatically generated information from the file IO
writer.KeepOriginalImageUIDOn()

# Copy relevant tags from the original meta-data dictionary (private tags are also
# accessible).
tags_to_copy = ["0010|0010", # Patient Name
                "0010|0020", # Patient ID
                "0010|0030", # Patient Birth Date
                "0020|000D", # Study Instance UID, for machine consumption
                "0020|0010", # Study ID, for human consumption
                "0008|0020", # Study Date
                "0008|0030", # Study Time
                "0008|0050", # Accession Number
                "0008|0060"  # Modality
]

modification_time = time.strftime("%H%M%S")
modification_date = time.strftime("%Y%m%d")

# Copy some of the tags and add the relevant tags indicating the change.
# For the series instance UID (0020|000e), each of the components is a number, cannot start
# with zero, and separated by a '.' We create a unique series ID using the date and time.
# tags of interest:
direction = resampled_image.GetDirection()
series_tag_values = [(k, series_reader.GetMetaData(0,k)) for k in tags_to_copy if series_reader.HasMetaDataKey(0,k)] + \
                 [("0008|0031",modification_time), # Series Time
                  ("0008|0021",modification_date), # Series Date
                  ("0008|0008","DERIVED\\SECONDARY"), # Image Type
                  ("0020|000e", "1.2.826.0.1.3680043.2.1125."+modification_date+".1"+modification_time), # Series Instance UID
                  ("0020|0037", '\\'.join(map(str, (direction[0], direction[3], direction[6],# Image Orientation (Patient)
                                                    direction[1],direction[4],direction[7])))),
                  ("0008|103e", series_reader.GetMetaData(0,"0008|103e") + " Processed-SimpleITK")] # Series Description

for i in range(resampled_image.GetDepth()):
    image_slice = resampled_image[:, :, i]
    # Tags shared by the series.
    for tag, value in series_tag_values:
        image_slice.SetMetaData(tag, value)
    # Slice specific tags.
    image_slice.SetMetaData("0008|0012", time.strftime("%Y%m%d")) # Instance Creation Date
    image_slice.SetMetaData("0008|0013", time.strftime("%H%M%S")) # Instance Creation Time
    image_slice.SetMetaData("0020|0032", '\\'.join(map(str, resampled_image.TransformIndexToPhysicalPoint((0, 0, i))))) # Image Position (Patient)
    image_slice.SetMetaData("0020,0013", str(i)) # Instance Number

    # Write to the output directory and add the extension dcm, to force writing in DICOM format.
    writer.SetFileName(os.path.join(out_path, str(i)+'.dcm'))
    writer.Execute(sitk.Cast(image_slice, sitk.sitkUInt16))