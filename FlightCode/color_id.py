###### VERSION 4.8.13 ######

###### Final testing version ######

# Script for determining the percentage of each color using PIL and using RGB representation.
# Pushes the associated files to the github repo specified in git_push()..

# INPUT: To run this code, simply enter "python3 color_id.py FILE_PATH", where FILE_PATH is the image you would like to process
# If you do not type anything after "color_id.py", the pi will take a picture automatically and use that for the processing

# OUTPUT:
#    Prints the number of pixels of different colors (RGB White Black other) in the original Image
#    Prints the percentage of pixels of each color (RGB, White) in the original Image,
#    relative to both the rest of the plastic and the posterboard
#    Creates and saves several pictures (.jpg) the most important of which are:
#        'new_image' + time string: the original image, but filtered into RGB White Black
#        'denoised' + time string: new_image, but cleaned up to remove some stray pixels
#        'overwrite' + time string: the original image, where the shapes have been turned white and everything else is black
#    Prints the number of pieces of plastic of each color and size in the image.
#    Prints the total runtime of the program.


#TODO: At the bottom of the script, set the variable YOUR_NAME to be your name (just first is fine). Also, make sure you do git pull
# before you run this script, because it will push to GitHub automatically once it's run.
# Also, you will need to install skimage before running this code. (At this point, technically you don't,
# so if you're having problems with it, just delete the "from skimage import measure" line (line 35 or so)

#TODO: Remember to adjust the brightness function, colors, and pixel width of the squares in your images. 
# These are marked with "TODO" comments, and put between #=====================# lines.
# You can also adjust other things, but be careful you don't break the code (just because it can be time consuming to fix).

#TODO: Please copy this file into another folder or directory so you're not editing this exact file.

from PIL import Image, ImageEnhance, ImageDraw, ImageFilter
import sys
import numpy as np
from numpy import asarray
from git import Repo
import os
import time
import math
from skimage import measure
from skimage.measure import label, regionprops

def git_push():
    # From the FlatSatChallenge, a function to automatically upload to GitHub
    try:
        repo = Repo('/home/nicom26/AstroBeeverPrivate') #TODO: MAKE SURE TO REPLACE "nicom26" you YOUR username
        repo.git.add('/home/nicom26/AstroBeeverPrivate') #TODO: SAME THING HERE
        repo.index.commit('New Commit')
        print('made the commit')
        origin = repo.remote('origin')
        print('added remote')
        origin.push()
        print('pushed changes')
    except:
        print('Couldn\'t upload to git')

def photograph():
    # Takes a picture using the Pi's camera
    # INPUT: None
    # OUTPUT: A .jpg image
    from picamera import PiCamera
    camera = PiCamera()
    
    time.sleep(1)
    variable = YOUR_NAME + fname + '.jpg'
    camera.capture(variable)
    print()
    print("Took a picture!")

def resize(image_path):
    # Resizes the image to the value specified
    img = Image.open(image_path)

    basewidth = 720                              # This is the value you would change BUT PLEASE DON'T

    wpercent = (basewidth / float(img.size[0]))
    hsize = int((float(img.size[1]) * float(wpercent)))
    img = img.resize((basewidth, hsize), Image.ANTIALIAS)
    img.save(YOUR_NAME + "resized_" + fname + '.jpg')
    print()
    print("Resized the picture!")
    print()

def compute_energy(img):
    """ Given a 2D array of color values, produces a 2D array with
    the energy at each pixel, where energy is defined as the sum
    of each's pixels neighbors differing in color from that pixel.

    INPUT:   img : numpy.ndarray, shape=(M, N)--An MxN array of color values.
    OUTPUT: numpy.ndarray, shape=(M, N)--An MxN array of energy values.
    """
    energies = np.zeros_like(img)

    energies[:-1] += img[:-1] != img[1:]           # below
    energies[1:] += img[1:] != img[:-1]            # above
    energies[:, :-1] += img[:, :-1] != img[:, 1:]  # right
    energies[:, 1:] += img[:, 1:] != img[:, :-1]   # left
    return energies

def get_neighbor_colors(img, pixel):
    """ Given a 2D array of color values and the position of a pixel,
    # returns a list of `pixel`'s neighboring color values.

    INPUT: img : numpy.ndarray, shape=(M, N)--An MxN array of color values
        pixel : tuple[int, int]
        The (r, c) index of the pixel whose neighbors to retrieve.
    OUTPUT": List[int]-- The color (or label) value of each of `pixel`'s neighbors.
    """
    neighbor_vals = []
    if pixel[0] > 0:
        neighbor_vals.append(img[pixel[0]-1, pixel[1]])
    if pixel[1] > 0:
        neighbor_vals.append(img[pixel[0], pixel[1]-1])
    if pixel[0] < img.shape[0]-1:
        neighbor_vals.append(img[pixel[0]+1, pixel[1]])
    if pixel[1] < img.shape[1]-1:
        neighbor_vals.append(img[pixel[0], pixel[1]+1])
    return neighbor_vals

def denoise_iter(noisy):
    """ Given a 2D array of color values, performs one step of the
    Iterated Conditional Modes algorithm, changing the color of
    the highest-energy pixel.
    INPUT: noisy : numpy.ndarray, shape=(M, N)--An MxN array of color values.
    OUTPUT: numpy.ndarray, shape=(M, N)--An MxN array of color values, after applying one step of ICM.
    """
    noisy = noisy.copy()
    # get the energy
    energies = compute_energy(noisy)

    # get the highest-energy pixel coordinates
    highest_energy = np.divmod(np.argmax(energies), noisy.shape[1])

    # compute the mode of the pixel's neighbors
    neighbors = get_neighbor_colors(noisy, highest_energy)
    (neighbor_labels, neighbor_counts) = np.unique(neighbors, return_counts=True)

    # assign the best label (mode of the neighbors) to the highest-energy pixel
    best_label = neighbor_labels[np.argmax(neighbor_counts)]
    noisy[highest_energy] = best_label
    return noisy

def denoise(noisy):
    # INPUT: The numpy array of a noisy image
    # OUTPUT: the numpy array of the denoised image
    num_iters = 0                    # how many iterations we have performed, to see progress
    cleaned_up = noisy.copy()        # the denoised image
    old = np.zeros_like(cleaned_up)  # the previous iteration, for a stopping condition

    while np.any(old != cleaned_up): # loop until no labels change values
        num_iters += 1
        if (num_iters%1000) == 0:    # print progress
            print(num_iters, 'Energy {}'.format(compute_energy(cleaned_up).sum()))
        old = cleaned_up.copy()
        cleaned_up = denoise_iter(cleaned_up)
    print("denoise ran", num_iters, "times.")
    return cleaned_up

def brighten(image_path):
    """ Brightens an image conditionally
    INPUT: an image
    OUTPUT: a brightened image
    counter for the actual values in the pixels (255, 0, 153, 175, etc.)
    """
    img = Image.open(image_path)
    array = asarray(img)
    sum_pix_vals = 0
    pixels = 0

    for x in np.nditer(array):
        pixels += 1
        sum_pix_vals += x

    avg_brightness = round((sum_pix_vals / (3 * pixels)), 2)
    print("The average brightness before enhancement is", avg_brightness)
    print()

    # TODO:
    # This is the code that controls the conditional brightness of the image.
    # If your background is really dark, but your poster board isn't, verify that the algorithm isn't brightnening 
    # your image further.
    # A factor greater than 1 brightens the image, and a factor less than 1 dims it. The factor can be between 0 and 2.
    
    #======================================#
    factor = 54/(avg_brightness * 1.1)
    
    if avg_brightness < 33:
        factor = 0.8
    #=======================================#
    
    img = Image.fromarray(array)
    enhancer = ImageEnhance.Brightness(img)
    im_output = enhancer.enhance(factor)

    enhancer = ImageEnhance.Sharpness(im_output)
    factor = 2
    img_s_1 = enhancer.enhance(factor)
    img_s_1.save(YOUR_NAME + "brightened_" + fname + '.jpg')



def DENOISE(image_path):
    """The main function that begins the calls to all the denoising sub-functions.
    Converts the input image to a numpy array for the sub-processing functions.
    Resizes, brightens, and then denoises the image

    INPUT: an image
    OUTPUT: The same image, but de-noised
    """
    image = Image.open(image_path)
    data = asarray(image)
    denoised_numpy_array = denoise(data)
    image2 = Image.fromarray(denoised_numpy_array)
    
    # Save the image based on if DENOISE is being called the first or second time
    if image_path == YOUR_NAME + 'pre_denoise_overwrite_' + fname + '.jpg':
        image2.save(YOUR_NAME + 'overwrite_' + fname + '.jpg')
    elif image_path == YOUR_NAME + 'resized_image_with_borders_' + fname + '.jpg':
        image2.save(YOUR_NAME + 'denoised_part_2_' + fname + '.jpg')
    else:
        image2.save(YOUR_NAME + 'denoised_' + fname + '.jpg')

################################################################################################

#TODO: Below are the functions which determine the colors of each pixel. If your red is showing up incorrectly,
# alter the "red" function. Likewuse, if any other color is being misidentified, edit the function for that color.

#=========================================================================#
def too_light(r, g, b):
    """ Identifies colors that are too light
    To be sure that it does not cannibalize from the white pixels, make sure this function
    is called AFTER the white(r, g, b) function
    """
    mxx = max(r, g, b)

    if r > 150 and g > 150:
        return True
    if r > 150 and b > 150:
        return True
    if b > 150 and g > 150:
        return True

    if (r+ g + b)/3 > 160:
        return True
    if (r + g + b) > 490 and abs(g - (((r + g + b) - mxx)/2)) < 30:
        return True

    rgb_tuple = (r, g, b)
    colors = {"green": (0, 200, 0), "blue": (0, 0, 255), "white": (240, 240, 240), "red": (255, 0, 0)}
    manhattan = lambda x,y : abs(x[0] - y[0]) + abs(x[1] - y[1]) + abs(x[2] - y[2]) 
    distances = {k: manhattan(v, rgb_tuple) for k, v in colors.items()}
    color = min(distances, key=distances.get)
    x = colors[color]
    if x == (240, 240, 240):
        return True

    return False

def brown(r, g, b):
    # Identifies Brown:
    if 200 < r < 220 and 75 < (g + b)/2 < 160:
        return True
    if 220 < r < 255 and 160 < (g + b)/2 < 200:
        return True
    if r < 180 and g + b > 300:
        return True
    if 135 < r < 210 and 55 < g < 85 and b < 30:
        return True
    if abs(r - (g + b)) < 30:
        return True
    return False

def too_dark(r, g, b):
    # Identifies colors that are too dark:
    # MUST BE RUN *AFTER* THE RGB DETECTORS, OTHERWISE IT WILL CANNIBALIZE THEM
    mxx = max(r, g, b)
    if mxx == r and mxx < 100:
        return True
    if mxx == g and mxx < 55:
        return True
    if mxx == b and mxx < 45:
        return True
    return False

def red(r, g, b):
    # identifies RED:
    mxx = max(r, g, b)
    if mxx == r and 190 < r and g < 120 and b < 150:
        return True
    if mxx == r and 170 < r and g < 120 and b < 130:
        return True
    if mxx == r and 130 < r < 180 and 47 < g < 90 and 100 < b < 145:
        return True
    if mxx == r and 150 < r and g < 120 and b < 105:
        return True
    if mxx == r and 120 < r and g < 90 and b < 90:
        return True
    if mxx == r and 80 < r and g < 60 and b < 65:
        return True
    
    # Accounts for purplish red
    if mxx == b and g < 75 and b-r < 20:
        return True

    return False

def purple_and_black(r, g, b):
    # Identifies dark purple and purplish black (this is made specially for you Emily lol)
    avg = (r + g + b)/3
    mxx = max(r, g, b)
    if 70 < mxx < 150:
        if abs(avg-r) < 15 and abs(avg-g) < 15 and abs(avg-b) < 15:
            return True
    if 40 < mxx < 71:
        if abs(avg-r) < 10 and abs(avg-g) < 10 and abs(avg-b) < 10:
            return True
    if mxx < 41:
        if abs(avg-r) < 5 and abs(avg-g) < 5 and abs(avg-b) < 5:
            return True
    return False

def green(r, g, b):
    # Identifies GREEN:
    mxx = max(r, g, b)
    if mxx == g and 100 < g and b < 90 and r < 90:
        return True
    if mxx == g and 70 < g and b < 70 and r < 75:
        return True
    if mxx == g and 80 < g < 95 and b < 85 and r < 75:
        return True
    if 40 <= g <= 70 and b < 40 and r < 25:
        return True
    if 40 <= g <= 70 and mxx == g and b < 55 and r < 40:
        return True
    if 20 < g < 40 and b < 17 and r < 15:
        return True
    
    # Accounting for the green that appears greenish-blue:
    if 110 < g < 140 and mxx == b and 130 < b < 150 and r < 65:
        return True
    if mxx == b and r < 50 and 95 < g:
        return True
    if mxx == b and b-g < 7 and b < 80:
        return True
    if mxx == b and 140 > b and r < 45 and b-g < 40:
        return True
    return False

    rgb_tuple = (r, g, b)
    colors = {"green": (0, 255, 0), "blue": (0, 0, 255), "white": (255, 255, 255), "red": (255, 0, 0)}
    manhattan = lambda x,y : abs(x[0] - y[0]) + abs(x[1] - y[1]) + abs(x[2] - y[2]) 
    distances = {k: manhattan(v, rgb_tuple) for k, v in colors.items()}
    color = min(distances, key=distances.get)
    x = colors[color]
    if x == (0, 255, 0):
        return True
    return False

def blue(r, g, b):
    # Identifies BLUE:
    mxx = max(r, g, b)
    if mxx == b and 190 < b and g < 130 and r < 75:
        return True
    if mxx == b and 115 < b and g < 130 and r < 75:
        return True
    if mxx == b and 40 < b and g < 90 and r < 75:
        return True
    if mxx == b and 25 < b and g < 20 and r < 15:
        return True
    rgb_tuple = (r, g, b)
    colors = {"green": (0, 200, 0), "blue": (0, 0, 255), "white": (250, 250, 250), "red": (255, 0, 0)}
    manhattan = lambda x,y : abs(x[0] - y[0]) + abs(x[1] - y[1]) + abs(x[2] - y[2])
    distances = {k: manhattan(v, rgb_tuple) for k, v in colors.items()}
    color = min(distances, key=distances.get)
    x = colors[color]
    if x == (0, 0, 255):
        return True
    return False

def white(r, g, b):
    # Identifies white:
    rgb_tuple = (r, g, b)
    colors = {"green": (230, 230, 230), "blue": (230, 230, 230), "white": (250, 250, 250), "red": (230, 230, 230)} 
    manhattan = lambda x,y : abs(x[0] - y[0]) + abs(x[1] - y[1]) + abs(x[2] - y[2])
    distances = {k: manhattan(v, rgb_tuple) for k, v in colors.items()}
    color = min(distances, key=distances.get)
    x = colors[color]
    if x == (250, 250, 250):
        return True
    return False

#=========================================================================#

def max_color(r, g, b):
    """ A function for classifying pixels as either red, green, blue, black, or white.
    Current weak point is really dark green, and hardwood floors that appear red
    As of right now, working on improving the detection and removal of brown, as well as the detection of the plastics
    if the image is on the darker side.
    Don't switch the order that the functions are called in as that might have an effect on the output color, since 
    there is some overlap between certain functions.

    INPUT: 3 values--the R, G, B of a pixel
    OUTPUT: A tuple containing RGB pixel values
    """
    # Returns purple
    if purple_and_black(r, g, b) == True:
        return (128, 0, 128)
    
    if green(r, g, b) == True:
        return (0, 255, 0)

    if red(r, g, b) == True:
        return (255, 0, 0)

    if blue(r, g, b) == True:
        return (0, 0, 255)
    
    # Returns brown in new_image and denoised
    if brown(r, g, b) == True:
        return (210, 105, 30)

    if white(r, g, b) == True:
        return (255, 255, 255)

    # Returns light blue in new_image and denoised
    if too_light(r, g, b) == True:
        return (135, 206, 250)

    if too_dark(r, g, b) == True:
        return (0, 0, 0)
    
    # Returns violet in new_image and denoised (this only happens if the pixel falls outside of the color ranges of 
    # all the color identifying functions)
    return (238,130,238)
    
#########################################################################################

def color_id(image_file):
    """ A function to determine the color percentages in an image, as well as count the nuber of plastic pieces

    INPUT: An image file
    OUTPUT: strings containing the number of pixels and percentages of each color;
    YOUR_NAME_new_file_TIMESTRING.jpg; YOUR_NAME_denoised_TIMESTRING.jpg; and YOUR_NAME_overwrite_TIMESTRING.jpg.
    """
    img = Image.open(image_file).convert("RGB")
    data = img.load()

    # Creating a blank image the same size as the original. The background color is set to light blue,
    # so anything that is not red, green, blue, or white will show up in new_image.jpg as light blue.
    # All of the light blue and black pixels are ignored when calculating percentages and results.
    blank = Image.new('RGB', (img.width, img.height), color = (0, 0, 0))
    new_image = blank.copy()
    overwrite = blank.copy()
    color_amount = {"red":0, "green":0, "blue":0, "white":0, "black":0, "light_blue":0, "other":0}

    # The counters for measuring the average brightness after enhancement
    sum_pix_vals = 0
    pixels = 0

    # Main processing loop
    for x in range(img.width):
        for y in range(img.height):
            new_color = max_color(data[x, y][0], data[x, y][1], data[x, y][2])
            new_image.putpixel((x,y), new_color)
            if new_color == (255, 0, 0):
                color_amount["red"] += 1
                overwrite.putpixel((x, y), (255, 255, 255))

            elif new_color == (0, 255, 0):
                color_amount["green"] += 1
                overwrite.putpixel((x, y), (255, 255, 255))

            elif new_color == (0, 0, 255):
                color_amount["blue"] += 1
                overwrite.putpixel((x, y), (255, 255, 255))

            elif new_color == (255, 255, 255):
                color_amount["white"] += 1
                overwrite.putpixel((x, y), (0, 0, 0))

            elif new_color == (0, 0, 0):
                color_amount["black"] += 1
                overwrite.putpixel((x, y), (0, 0, 0))

            elif new_color == (135, 206, 250):
                color_amount["light_blue"] += 1
                overwrite.putpixel((x, y), (0, 0, 0))
            else:
                color_amount["other"] += 1
                overwrite.putpixel((x, y), (0, 0, 0))

            sum_pix_vals += (data[x, y][0] + data[x, y][1] + data[x, y][2])
            pixels += 1

    avg_brightness_2 = round((sum_pix_vals / (3 * pixels)), 2)
    print("The average brightness after enhancement is", avg_brightness_2)

    str_2 = YOUR_NAME + 'new_image_' + fname + '.jpg'
    new_image.save(str_2)
    DENOISE(str_2)
    
    overwrite.save(YOUR_NAME + 'pre_denoise_overwrite_' + fname + '.jpg')
    DENOISE(YOUR_NAME + 'pre_denoise_overwrite_' + fname + '.jpg')

    print()
    print("color_amount is ", color_amount)
    
    # If there is no white at all, assume the picture was too dark and turn the "too light" pixels
    # into white
    if color_amount["white"] < 100:
        color_amount["white"] = color_amount["light_blue"]

    # Finding the percentage of the plastic relative to the poster board
    num_pix = color_amount["red"] + color_amount["green"] + color_amount["blue"]
    perc_plastic = num_pix / (color_amount["white"] + num_pix)

    # Finding the percentages of the plastic pieces relative to each other
    total_pix = color_amount["red"] + color_amount["green"] + color_amount["blue"]
    perc_red = color_amount["red"]/total_pix
    perc_green = color_amount["green"]/total_pix
    perc_blue = color_amount["blue"]/total_pix

    # Percentage results!!
    print()
    print("The percentage of plastic on the posterboard is", round(100*perc_plastic, 2), "%")
    print()
    print("The percentage of red is",round(100*perc_red,2),"%")
    print("The percentage of green is",round(100*perc_green,2),"%")
    print("The percentage of blue is",round(100*perc_blue,2),"%")
    print()


    """ finds the squares in an image, determines their size by assuming the distance from the floor is constant,
        and therefore that each square is a set size of pixels.
        Assumes base width of resized image is 720, but i'll try to take the image size into account
    """
    red = color_amount["red"]
    green = color_amount["green"]
    blue = color_amount["blue"]

    #TODO: THESE ARE THE VALUES THAT YOU CHANGE, DEPENDING ON HOW BIG THE SQUARES SHOW UP IN YOUR PICS
    
    #=================================================#
    # The length of one side of a square, in pixels, in an image with a base width of 720p.
    small_side = 16
    med_side = 35
    big_side = 59
    #=================================================#
    
    # Kindof irrelevant now, but limits how close the total has to be to the calculated total.
    # Changing it upward shouldn't have much effect; changing it below 100 will probably mess the later
    # function up sometimes with poorer quality/blurrier images
    buffer = 175
        
    # The maximum number of pieces of each size <<PLUS ONE>> (because it makes using the range() function easier)
    max_small = 6       # There are only 5 small pieces of each color
    max_med = 5         # There are only 4 medium pieces of each color
    max_big = 3         # There are only 2 large pieces of each color
    
    small = small_side**2
    med = med_side**2
    big = big_side**2

    red_list = square_list(red, small, med, big, buffer, max_small, max_med, max_big)
    green_list = square_list(green, small, med, big, buffer, max_small, max_med, max_big)   
    blue_list = square_list(blue, small, med, big, buffer, max_small, max_med, max_big)

    # Printing the results:
    print("Small red squares:", str(red_list[0]))
    print("Medium red squares:", str(red_list[1]))
    print("Large red squares:", str(red_list[2]))
    print()

    print("Small green squares:", str(green_list[0]))
    print("Medium green squares:", str(green_list[1]))
    print("Large green squares:", str(green_list[2]))
    print()
    
    print("Small blue squares:", str(blue_list[0]))
    print("Medium blue squares:", str(blue_list[1]))
    print("Large blue squares:", str(blue_list[2]))
    print()

def square_list(pixels, small, med, big, buffer, max_small, max_med, max_big):
    """ Counts the number of squares of different sizes.
        INPUT: a ton of variables, representing:
        pixel = number of pixels
        small, med, and big are the areas of those respective squares
        buffer = the buffer defined a few dozen lines earlier
        max_small, max_med, and max_big: the maximum number of pieces of plastic of each color and size
        
        OUTPUT: a list containg the number of small, medium, and big pieces of that color
    """
    big_lst = []
    
    for x in range(max_small):
        for y in range(max_med):
            for z in range(max_big):
                if (pixels - buffer) < (small*x + med*y + big*z) < (pixels + buffer):
                    diff = abs(pixels - (small*x + med*y + big*z))
                    big_lst += [[diff, [x, y, z]]]
                    
    # if the color isn't actually there, make sure it doesn't count:
    if pixels < 175:
        return [0, 0, 0]
    
    # Returns the number of small, medium, and big pieces
    if len(big_lst) > 0:
        mxx = min(big_lst)
        return mxx[1]
    return [0, 0, 0]
    return [0, 0, 0]
#################################################################

# MAIN SCRIPT:

YOUR_NAME = "Nico_" #TODO: CHANGE TO YOUR NAME OR THINGS WILL BE CONFUSING

start_time = time.time()

# Makes a time string, to help with image calibration:
fname = (time.strftime("%b-%d_%H-%M-%S"))

# Calling the main function:
if __name__ == '__main__':
    if len(sys.argv) == 1:
        photograph()
        resize(YOUR_NAME + fname + '.jpg')
        brighten(YOUR_NAME + "resized_" + fname + '.jpg')
        color_id(YOUR_NAME + 'brightened_' + fname + '.jpg') #TODO 

    else:
        resize(*sys.argv[1:])
        brighten(YOUR_NAME + "resized_" + fname + '.jpg')
        color_id(YOUR_NAME + 'brightened_' + fname + '.jpg')

# Timing the runtime of the script
time_2 = (time.time() - start_time)
time_2 = round(time_2, 2)
print('Runtime without git_push(): %s seconds' % (time_2))
print()

git_push()

print()
time = (time.time() - start_time)
time = round(time, 2)
print("Total runtime: --- %s seconds ---" % (time))
print()
