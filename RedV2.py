import praw
import requests
import os
import re
import sys
from time import time


def linklistparser(link_list):
    parsed_link_list = []
    for link in link_list:
        if "eroshare" in link:
            continue
        if ".html" in link:
            continue
        if re.findall(r'\.[a-zA-Z0-9]+$', link):
            if "gifv" in link:
                link = link[:-1]
            parsed_link_list.append(link)
        elif "gfycat" in link:
            try:
                link = re.findall(r'[a-zA-Z]+$', link)[0]
            except IndexError:
                print("error " + link)
            try:
                r = requests.get("https://gfycat.com/cajax/get/" + link)
            except:
                continue

            if "mp4Url" in r.text:
                prefix = re.findall(r'(?<=mp4Url":"https:\\\/\\\/)[a-z]+', r.text)[0]
                name = re.findall(r'(?<=\/)[a-zA-Z]+(?=.mp4)', r.text)[0]
                parsed_link_list.append("https://" + prefix + ".gfycat.com/" + name + ".mp4")

        elif "imgur" in link and "/a/" not in link:
            parsed_link_list.append(link + ".png")

        elif "i.redd" in link:
            parsed_link_list.append(link + ".png")

        elif "imgur" in link and "/a/" in link:
            album_source = requests.get(link)
            album_link_list = re.findall(r'("hash":")(.+?)("ext":"[.a-zA-Z0-9]+)', str(album_source.text))
            tmp = []
            for i in album_link_list:
                link_part = re.findall(r'(?<=hash":"\', \')[a-zA-Z0-9]+', str(i))
                extension_part = re.findall(r'(?<=ext":")[.a-zA-Z0-9]+', str(i))
                if "gifv" in extension_part:
                    extension_part = ".gif"
                tmp.append("https://i.imgur.com/{}{}".format(link_part[0], extension_part[0]))
            for i in range(int(len(tmp)/2)):
                parsed_link_list.append(tmp[i])

        else:
            print(link + " failed to parse")

    return parsed_link_list


def downloadlinks(link_list, sub, subcategory, supercategory):
    start_time = time()
    if " " in supercategory:
        ind = supercategory.find(" ")
        supercategory = supercategory[:ind] + "_" + supercategory[ind+1:]
    if " " in subcategory:
        ind = subcategory.find(" ")
        subcategory = subcategory[:ind] + "_" + subcategory[ind+1:]
    i = 1
    print("\nE:\RedditV2\porn\{}\{}\{}".format(supercategory, subcategory, sub))
    if not os.path.exists("porn" + "\\" + supercategory + "\\" + subcategory + "\\" + sub):
        os.makedirs("porn" + "\\" + supercategory + "\\" + subcategory + "\\" + sub)
    downsize = 0
    for link in link_list:
        file_format = re.findall(r'(\.[a-zA-Z0-9]+)$', link)[0]

        if os.path.exists("porn" + "\\" + supercategory + "\\" + subcategory + "\\" + sub + "\\" + str(i) + file_format):
            print(i, link + " already exists")
            i += 1
            continue

        try:
            r = requests.get(link)
        except:
            i += 1
            continue

        if "removed" not in r.url:
            f = open("porn" + "\\" + supercategory + "\\" + subcategory + "\\" + sub + "\\" + str(i) + file_format, 'wb')
            for chunk in r.iter_content(chunk_size=255):
                if chunk:
                    f.write(chunk)
            statinfo = os.stat("porn" + "\\" + supercategory + "\\" + subcategory + "\\" + sub + "\\" + str(i) + file_format)
            print("{} {} ({} mb)".format(str(i), link, statinfo.st_size / 1000000))
            downsize += statinfo.st_size
            i += 1
        else:
            print(link + " was removed")
    print(str(downsize/1000000) + " MB downloaded in {:.2f} seconds\n".format(time()-start_time))


def fetchlinks(reddit, sub_list, subcategory, supercategory, post_number):
    print()
    for sub in sub_list:
        start_time = time()
        print(sub)
        link_list = []
        i = 1
        try:
            subreddit = reddit.subreddit(sub)
            for submission in subreddit.top(limit=post_number):
                sys.stdout.write("{} - {}, {}".format(i, submission, submission.url))
                if "/a/" in submission.url:
                    sys.stdout.write(" Album link\n")
                else:
                    sys.stdout.write("\n")
                i += 1
                link_list.append(submission.url)
            print("\n{} links found in {:.2f} seconds".format(len(link_list), time()-start_time))
            start_time = time()
            link_list = linklistparser(link_list)
            print("{} links successfully parsed in {:.2f} seconds".format(len(link_list), time()-start_time))
            downloadlinks(link_list, sub, subcategory, supercategory)
        except:
            print("https://reddit.com/r/" + sub + " Error\n")
            continue


def dictionaryinit():
    with open("pornlist", "r") as f:
        x = str(f.readlines())
    categories = re.findall(r'(?<=@@\\n\', \')[\w\s]+(?=\\n)', x)
    d1 = {}
    d2 = {}

    for i in categories:
        category_block = str(re.findall(r'(@@\\n\'\, \'{})(.+?)(@@)'.format(i), x))
        subcategories = re.findall(r'(?<=##)(.+?)(?=\\\\n)', category_block)
        for ii in subcategories:
            subcategory_block = str(re.findall(r'(##)({})(.+?)((##)|(@@))'.format(ii), category_block))
            subreddits = re.findall(r'(?<=/r/)[\w]+', subcategory_block)
            d1[ii] = subreddits
        d2[i] = d1
        d1 = {}
    print(d2)
    return d2


def getredditsession():
    reddit = praw.Reddit(client_id='3d3fhNknZsPbXw',
                         client_secret='Wlj_qXsqqAmyzd3Ss67X0E3ngFs',
                         user_agent='android:com.example.myredditapp:v1.2.3 (by /u/Jatariee)',
                         username='Jatariee',
                         password='Starwars3205')
    return reddit


def getsupercategory(d):
    print()
    print()
    for i in d:
        print(i)
    while True:
        supercat = input("\nEnter Supercategory: ")
        if supercat == "*":
            return supercat
        if supercat not in d:
            print("\nInvalid")
            continue
        return supercat


def getsubcategory(d, supercat):
    print(supercat)
    print(d[supercat])
    for i in d[supercat]:
        print(i)
    while True:
        subcat = input("\nEnter Subcategory: ")
        if subcat == "*":
            return subcat
        if subcat not in d[supercat]:
            print("\nInvalid")
            continue
        return subcat


def getsubredditlist(d, supercat, subcat):
    print()
    for i in d[supercat][subcat]:
        print(i)
    sublist = list(input("Enter subs: ").split(" "))
    if "*" in sublist:
        sublist = d[supercat][subcat]
    print(sublist)
    return sublist


def downallsuper(reddit, d, post_count):
    for i in d:
        for ii in d[i]:
            sublist = d[i][ii]
            fetchlinks(reddit, sublist, i, ii, post_count)


def downallsub(reddit, d, supercat, post_count):
    for i in d[supercat]:
        sublist = d[supercat][i]
        fetchlinks(reddit, sublist, i, supercat, post_count)


def main():
    reddit = getredditsession()
    d = dictionaryinit()
    post_count = int(input("\nEnter Num Posts: "))
    supercategory = getsupercategory(d)
    if supercategory == "*":
        downallsuper(reddit, d, post_count)
    else:
        subcategory = getsubcategory(d, supercategory)
        if subcategory == "*":
            downallsub(reddit, d, supercategory, post_count)
        else:
            sublist = getsubredditlist(d, supercategory, subcategory)
            if sublist == "*":
                sublist = d[supercategory][subcategory]
            fetchlinks(reddit, sublist, subcategory, supercategory, post_count)

if __name__ == "__main__":
    main()
