import wx


def lerp(val1, val2, amount):
    "Simple linear interpolation between two numbers"

    return (1-amount)*val1 + amount*val2



def MixColors(color1, color2, amount):
    "Mix colors by amount"

    r = int(lerp(color1.red, color2.red, amount))
    g = int(lerp(color1.green, color2.green, amount))
    b = int(lerp(color1.blue, color2.blue, amount))
    return wx.Colour(r, g, b)


def IconFromSymbolic(image:wx.Image, color:wx.Colour):
    new_image = image.Copy()

    c_r = color.Red()
    c_g = color.Green()
    c_b = color.Blue()

    for x in range(0, new_image.Width):
        for y in range(0, new_image.Height):
            r = new_image.GetRed(x,y)
            g = new_image.GetRed(x,y)
            b = new_image.GetRed(x,y)

            if r == 128 and g == 128 and b == 128:
                new_image.SetRGB(x, y, c_r, c_g, c_b)

    return new_image


def SizeToString(size):
    if size < 1000:
        return "{} B".format(size)
    elif size < 1000000:
        return "{} KB".format(round(size/1000))
    elif size < 10000000:
        return "{} MB".format(round(size/1000000, 1))
    elif size < 1000000000:
        return "{} MB".format(round(size/1000000))
    elif size < 1000000000000:
        return "{} GB".format(round(size/1000000000, 1))
    elif size < 1000000000000000:
        return "{} TB".format(round(size/1000000000000, 2))
    elif size < 1000000000000000000:
        return "{} PB".format(round(size/1000000000000000, 3))
    elif size < 1000000000000000000000:
        return "{} EB".format(round(size/1000000000000000000, 4))
    else:
        return "{} B".format(size)


def SecondsToString(seconds_in):
    total   = seconds_in
    seconds = total % 60
    total   = total - seconds
    hours   = int(total / 3600)
    total   = int(total - (hours * 3600))
    minutes    = int(total / 60)

    if seconds_in < 60:
        return "{} s".format(seconds)
    elif seconds_in < 3600:
        return "{}:{:02}".format(minutes, seconds)
    else:
        return "{}:{:02}:{:02}".format(hours, minutes, seconds)

def CleanFilename(filename):
    return filename.strip().replace('\\','_').replace('/', '_').replace(':', '').replace('*', '').replace('?', '').replace('"', '').replace('<', '').replace('>', '').replace('|', '')
