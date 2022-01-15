#
# This file contains functions dealing with notes dedicated to Education purposes
# Like color coded sticky notes...
#

import os
import hou
import importlib

from past.utils import old_div
import nodegraphutils as utils
import sidefxedu_nodegraphview as edu_nodegraphview

try:
  reload(edu_nodegraphview)
except NameError:
  from importlib import reload
  reload(edu_nodegraphview)



# define colors
COLOR_BG = {
    "bestpractice": (255, 119, 0),
    "info": (162, 84, 255),
    "tip": (105, 204, 0),
    "warning": (255, 51, 0)
}
COLOR_TXT = {
    "bestpractice": (255, 255, 255),
    "info": (255, 255, 255),
    "tip": (255, 255, 255),
    "warning": (255, 255, 255)
}
SIDEFXEDU_QUICKMARK_KEY = 'sidefxedu_quickmark_'
IMAGE_BOUNDING_RECT = hou.BoundingRect(0.0, -0.2, -1.0, 0.8)
# NUMBER_STICKER_ROOT_PATH='${SIDEFXLABS}/misc/stickers/Font/SIDEFX_CUSTOM_EMBLEMS '
NUMBER_STICKER_ROOT_PATH='${SIDEFXLABS}/misc/stickers/Edu/number_'

def normalize_color(color):
    return tuple(x/255.0 for x in color)

# create a sticky info in current node
def createNotes(kwargs, stickytype="info"):

    ctrlclick = kwargs['ctrlclick']
    shiftclick = kwargs['shiftclick']
    altclick = kwargs['altclick']
    cmdclick = kwargs['cmdclick']

    stickytype = 'info'
    if(ctrlclick):
        stickytype = 'warning'
    elif(shiftclick):
        stickytype = 'bestpractice'
    elif(altclick):
        stickytype = 'tip'

    # get the network editor pane
    pane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)

    # get the current node in the network editor pane
    node = pane.pwd()
    position = pane.visibleBounds().center()

    sticky = node.createStickyNote()
    sticky.setBounds(hou.BoundingRect(0, 0, 4, 4))
    sticky.setPosition(position)
    sticky.setText(("#%s" % stickytype))
    sticky.setColor(hou.Color(normalize_color(COLOR_BG[stickytype])))
    sticky.setTextColor(hou.Color(normalize_color(COLOR_TXT[stickytype])))

class Quickmarks(object):

    # TODO:
    # - delete all previous quickmarks when creating new ones
    # - use quickmark().jump() instead of jumpTo(value)

    def __init__(self):
        super(Quickmarks, self).__init__()
        self._pane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
        self._qmlist = []
        self._qmcurrent = 0

    def reset(self):
        self._qmcurrent = 0

    def updateQmlist(self, keyword=SIDEFXEDU_QUICKMARK_KEY):
        self._qmlist = [int(qm.replace(keyword, '')) for qm in self.listQuickmarks()]
        self._qmlist.sort()

    def listQuickmarks(self, keyword=SIDEFXEDU_QUICKMARK_KEY):
        qmlist = [key for key in hou.node('/').userDataDict().keys() if keyword in key]
        return qmlist

    def createQuickMark(self, item, index, quickMarkKey):
        # Define the network
        net = item.parent() # net = self._pane.pwd()

        # Define the visualization bounds (frame the item in the network)
        pos = item.position() + hou.Vector2(0, item.size().y())
        bounds = hou.BoundingRect(pos[0], pos[1], pos[0], pos[1])
        # Adjust the bounds so we end up at roughly the "default" zoom level.
        minwidth = old_div(self._pane.screenBounds().size().x(), utils.getDefaultScale())
        minheight = old_div(self._pane.screenBounds().size().y(), utils.getDefaultScale())
        if bounds.size().x() < minwidth:
            expandVec = hou.Vector2((minwidth - bounds.size().x()) * 0.5, 0.0)
        if bounds.size().y() < minheight:
            expandVec += hou.Vector2(0.0, (minheight - bounds.size().y()) * 0.5)
        bounds.expand(expandVec)

        # Define the items to
        items = [item]
        currentnode = item if isinstance(item, hou.Node) else None
        edu_nodegraphview.setQuickMark(index, edu_nodegraphview.QuickMark(net, bounds, items, currentnode))
        self.updateQmlist()

    def deleteQuickmarks(self, keyword=SIDEFXEDU_QUICKMARK_KEY):
        self.updateQmlist()

        # get the network editor
        pane = self._pane

        # collect background images
        images = []
        bgimages = pane.backgroundImages()
        bgimagepaths = [image.path() for image in bgimages]
        images.extend(bgimages)
        # for image in images:
        #     print(image)

        for k in hou.node('/').userDataDict().keys():
            # print('k = %s' % k)
            if keyword in k:
                hou.node('/').destroyUserData(k)

                index = int(k.replace(keyword, ''))
                fullpath = os.path.expandvars(NUMBER_STICKER_ROOT_PATH+'%02d.png' % index)
                try:
                    # if the image is used, remove it
                    id = bgimagepaths.index(fullpath)
                    # print('id = %d' % id)
                    images.pop(id)
                    bgimagepaths.pop(id)
                except:
                    # if not, don't do anything
                    pass

            # set the background images
            pane.setBackgroundImages(images)

    def createBgImage(self, fullpath, itempath, boundingRect):
        """ Create a background image and add it to the list. """
        image = hou.NetworkImage()
        image.setPath(fullpath)
        image.setRelativeToPath(itempath)
        image.setRect(IMAGE_BOUNDING_RECT)
        return image

    def numberItems(self):
        """ This code attaches number background images to the selected network items. """

        # get the network editor
        pane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)

        # first delete all quickmarks
        self.deleteQuickmarks()

        # collect already existing images
        images = []
        bgimages = pane.backgroundImages()
        bgimagepaths = [image.path() for image in bgimages]
        images.extend(bgimages)

        # create images
        index = 1
        items = hou.selectedItems()
        for item in items:
            # define image path (must be full path)
            fullpath = os.path.expandvars(NUMBER_STICKER_ROOT_PATH+'%02d.png' % (index))
            # print(fullpath)

            # create a background image and add it to the list
            images.append(self.createBgImage(fullpath, item.path(), IMAGE_BOUNDING_RECT))

            # create a quickmark
            self.createQuickMark(item, index, SIDEFXEDU_QUICKMARK_KEY)

            # move index forward
            index += 1

        # set the background images
        pane.setBackgroundImages(images)

    def appendNumberItems(self):
        """ This code append a new quickmark. """

        # get the network editor
        pane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)

        # collect already existing images
        images = []
        bgimages = pane.backgroundImages()
        bgimagepaths = [image.path() for image in bgimages]
        images.extend(bgimages)

        # collect nodes with background image attached to them
        itemswithimage = [image.relativeToPath() for image in bgimages]
        # print(itemswithimage)

        # update quickmark list
        self.updateQmlist()

        # create images
        index = self._qmlist[-1]+1 if self._qmlist else 1
        selectedItems = hou.selectedItems()
        for item in selectedItems:
            # print(item.path())
            # if the item already has an image attached to it, skip it
            if item.path() not in itemswithimage:
                # define image path (must be full path)
                fullpath = os.path.expandvars(NUMBER_STICKER_ROOT_PATH+'%02d.png' % (index))

                # try:
                #     # if the image number is already used, remove it
                #     id = bgimagepaths.index(fullpath)
                #     images.pop(id)
                #     bgimagepaths.pop(id)
                # except:
                #     # if not, don't do anything
                #     pass

                # create a background image and add it to the list
                images.append(self.createBgImage(fullpath, item.path(), IMAGE_BOUNDING_RECT))

                # define a quickmark
                self.createQuickMark(item, index, SIDEFXEDU_QUICKMARK_KEY)

                # move index forward
                index += 1

        # set the background images
        pane.setBackgroundImages(images)

    def clear(self):
        # delete all quickmarks
        self.deleteQuickmarks()

    def jumpToNext(self):
        value = min(self._qmlist[-1], self._qmcurrent+1)
        self.jumpTo(value)
        # print("Jump to next (%d)" % value)

    def jumpToPrev(self):
        value = max(self._qmlist[0], self._qmcurrent-1)
        self.jumpTo(value)
        # print("Jump to prev (%d)" % value)

    def jumpToFirst(self):
        self.updateQmlist()
        if len(self._qmlist):
            value = self._qmlist[0]
            self.jumpTo(value)

    def jumpToLast(self):
        self.updateQmlist()
        if len(self._qmlist):
            value = self._qmlist[-1]
            self.jumpTo(value)

    def jumpTo(self, value):
        self._qmcurrent = value
        edu_nodegraphview.jumpToQuickMark(self._pane, value)
        # print("Jump to quickmark %d" % value)

    def jumpToQuickMark(editor, index):
        quickmark = getQuickMark(index)
        createUndoQuickMark(editor)
        if quickmark is not None:
            quickmark.jump(editor)
