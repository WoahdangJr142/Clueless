from PIL import Image, ImageColor
from discord.ext import commands
import discord
from utils.setup import stats
import requests
from io import BytesIO

class ColorBreakdown(commands.Cog):
    def __init__(self,client):
        self.client = client

    @commands.command(description="Amount of pixels for each color in an image.",
        usage="<image|url>")
    async def colors(self,ctx,url=None):
        # if no url in the command, we check the attachments
        if url == None:
            if len(ctx.message.attachments) == 0:
                return await ctx.send("❌ You must give an image or url to add.")
            if "image" not in ctx.message.attachments[0].content_type:
                return await ctx.send("❌ Invalid file type. Only images are supported.")
            url = ctx.message.attachments[0].url

        # getting the image from url
        try:
            response = requests.get(url)
        except (requests.exceptions.MissingSchema, requests.exceptions.InvalidURL, requests.exceptions.InvalidSchema, requests.exceptions.ConnectionError):
            return await ctx.send("❌ The URL you have provided is invalid.")
        if response.status_code == 404:
            return await ctx.send( "❌ The URL you have provided leads to a 404.")

        input_image = Image.open(BytesIO(response.content))

        tab = color_amount(input_image)
        tab_formated = "```\n" + format_color_breakdown(tab,["Color","Qty"],["^",">"]) + "```"

        emb = discord.Embed(title="Color Breakdown",description=tab_formated)

        await ctx.send(embed=emb)

def setup(client):
    client.add_cog(ColorBreakdown(client))

def color_amount(img):
    ''' Find the amount of pixels for each color in an image

    return a list of tuple of colors like [*(color_name,amount)] '''
    width,lenght = img.size
    colors = {}
    for x in range(width):
        for y in range(lenght):
            pixel_color = img.getpixel((x,y))
            if pixel_color[-1] == 255:
                pixel_color = pixel_color[:3]
                if pixel_color not in colors:
                    colors[pixel_color] = 1
                else:
                    colors[pixel_color] += 1
    colors_pxls = rgb_to_pxlscolor(colors)
    colors_pxls_sorted = sorted(colors_pxls.items(), key=lambda x: x[1],reverse=True) 
    return colors_pxls_sorted

def rgb_to_pxlscolor(rgb_dict):
    ''' Convert a dictionary in the format {*(RGB:amount)} to {*(color_name:amount)}

    color_name is a pxls.space color name, if the RGB doesn't match,
    the color_name will be the hex code'''
    res = {}
    for rgb in rgb_dict:
        
        for pxls_color in stats.get_palette():
            found = False
            if rgb == ImageColor.getcolor('#' + pxls_color["value"],'RGB'):
                res[pxls_color["name"]] = rgb_dict[rgb]
                found = True
                break
        if found == False:
            res[rgb_to_hex(rgb)] = rgb_dict[rgb]
    return res

def rgb_to_hex(rgb):
    ''' convert a RGB tuple to the matching hex code
    ((255,255,255) -> #ffffff)'''
    str = '#' + '%02x'*len(rgb)
    return str % rgb

def format_color_breakdown(table,column_names,alignments=None):
    ''' Format the color table in a string to be printed '''
    if not table:
        return
    if len(table[0]) != len(column_names):
        raise ValueError("The number of column in table and column_names don't match.")
    # find the longest columns
    table.insert(0,column_names)
    longest_cols = [
        (max([len(str(row[i])) for row in table]) + 1)
        for i in range(len(table[0]))]

    # format the header
    LINE = "-"*(sum(longest_cols) + len(table[0]*2))

    # format the body
    if not alignments:
        row_format = " | ".join(["{:>" + str(longest_col) + "}" for longest_col in longest_cols])
        title_format = " | ".join(["{:^" + str(longest_col) + "}" for longest_col in longest_cols])

    else:
        row_format = "| ".join([f"{{:{alignments[i]}" + str(longest_col) + "}" for i,longest_col in enumerate(longest_cols)])
        title_format = row_format

    str_table = f'{title_format.format(*table[0])}\n{LINE}\n'

    for row in table[1:]:
        str_table += row_format.format(*row) + "\n"
    return str_table
