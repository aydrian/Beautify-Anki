# Author: C9HDN
# Get reviewer class

from __future__ import annotations

from anki.errors import DeckRenameError
from anki.lang import _, ngettext
from anki.rsbackend import TR
from anki.utils import ids2str , isMac, isLin
from anki.hooks import wrap
import anki.sched, anki.schedv2

import aqt
from aqt import AnkiQt, gui_hooks
from aqt.utils import askUser, getOnlyText, openLink, shortcut, showWarning, tr , openHelp , showWarning 

from aqt.deckbrowser import DeckBrowser , DeckBrowserBottomBar
from aqt.overview import Overview , OverviewContent
from aqt.toolbar import Toolbar , BottomBar

from aqt import mw


from aqt.qt import *
from aqt.overview import Overview


from copy import deepcopy
from dataclasses import dataclass
from typing import Any


from .helpers import *
from .styles import *
from .stats import run 

run()



#############################################################################################





def renderDeckTree(self, nodes,depth, _old,):
    if not nodes:
        return ""
    else:
        buf = ""
    nameMap = self.mw.col.decks.nameMap()
    for node in nodes:
        buf += self._deckRow(node, depth, len(nodes), nameMap)
    return buf

def deckRow(self, node, depth, cnt, nameMap , _old):
    name, did, due, lrn, new, children = node
    deck = self.mw.col.decks.get(did)
    if did == 1 and cnt > 1 and not children:
        # if the default deck is empty, hide it
        if not self.mw.col.db.scalar("select 1 from cards where did = 1"):
            return ""
    # parent toggled for collapsing
    for parent in self.mw.col.decks.parents(did, nameMap):
        if parent["collapsed"]:
            buff = ""
            return buff
    prefix = "-"
    if self.mw.col.decks.get(did)["collapsed"]:
        prefix = "+"
    due += lrn

    def indent():
        return "&nbsp;" * 6 * depth

    if did == self.mw.col.conf["curDeck"]:
        klass = "deck current"
    else:
        klass = "deck"
    buf = "<li class='collection-item avatar row %s' id='%d'>" % (klass, did)
    # deck link
    if children:
        collapse = (
            "<a class='collapse padding' href=# onclick='return pycmd(\"collapse:%d\")'>%s</a>"
            % (did, prefix)
        )
    else:
        collapse = "<span class=collapse></span>"
    if deck["dyn"]:
        extraclass = "filtered"
    else:
        extraclass = ""
    buf += """
          <img src="assets/deck_icons/%s.png" alt="" class="circle">
    <span  class='col s7 decktd ' colspan=5>%s%s<a class="deck padding %s"
    href=# onclick="return pycmd('open:%d')">%s</a></span>""" % (
        name,
        indent(),
        collapse,
        extraclass,
        did,
        name,
    )
    # due counts
    def nonzeroColour(cnt, klass):
        if not cnt:
            klass = "zero-count"
        if cnt >= 1000:
            cnt = "1000+"
        return f'<span class="{klass}">{cnt}</span>'

    buf += " <span class='col s2 ' align=center>%s</span><span class='col s2 ' align=center>%s</span> " % (
        nonzeroColour(due, "review-count"),
        nonzeroColour(new, "new-count"),
    )
    # options
    buf += (
        "<span align=center class='opts col s1'><a onclick='return pycmd(\"opts:%d\");'>"
        "<img src='/assets/gears.svg' class=gears></a></span></li>" % did
    )
    # children
    buf += self._renderDeckTree(children, depth + 1)
    return buf

    def _topLevelDragRow(self):
        return "<tr class='top-level-drag-row'><span colspan='6'>&nbsp;</span></tr>"



DeckBrowser.drawLinks = [
        ["", "shared", _("<i class='material-icons left'>cloud_download</i> Get Shared")],
        ["", "create", _("<i class='material-icons left'>create_new_folder</i>Create Deck")],
        ["Ctrl+I", "import", _("<i class='material-icons left'>file_upload</i>Import File")],  # Ctrl+I works from menu
    ]

def drawButtons(self,_old):
    buf = ""
    drawLinks = deepcopy(self.drawLinks)
    for b in drawLinks:
        if b[0]:
            b[0] = _("Shortcut key: %s") % shortcut(b[0])
        buf += """
<a class='waves-effect waves-light btn-small' title='%s' onclick='pycmd(\"%s\");'> %s </a>""" % tuple(
            b
        )
    self.bottom.draw(
        buf=buf,
        link_handler=self._linkHandler,
        web_context=DeckBrowserBottomBar(self),
    )




Toolbar. _body = """
<link rel="stylesheet" type="text/css" href="assets/materialize.css">
<style>
{}
</style>

<nav class='teal lighten-2'  width=100%%>
<tr>
<td class=tdcenter align=center>%s</td>
</tr></nav>
""".format(toolbar_style)

DeckBrowser._body = """'
<link rel="stylesheet" type="text/css" href="assets/materialize.css">
<style>
{}
</style>
<center class="container">

<div class=row>

<div class="col s8">
<ul class=" card collection highlight" cellspacing=0 cellpading=3>
%(tree)s
</ul>
</div>

<div class="col s4">
%(stats)s


</div>
</center>
<script src="assets/script.js"></script>

""".format(style)


BottomBar._centerBody = """
<style>
{}
</style>
<link rel="stylesheet" type="text/css" href="assets/materialize.css">
<center id=outer><div width=100%% id=header><td align=center>
%s</td></div></center>
""".format(bottom_bar_style)


DeckBrowser._renderDeckTree = wrap(DeckBrowser._renderDeckTree , renderDeckTree, "around")
DeckBrowser._deckRow = anki.hooks.wrap(DeckBrowser._deckRow, deckRow, 'around')
DeckBrowser._drawButtons = anki.hooks.wrap(DeckBrowser._drawButtons, drawButtons, 'around')


#############################################################################################



def renderOverViewPage(self , _old):
    but = self.mw.button
    deck = self.mw.col.decks.current()
    self.sid = deck.get("sharedFrom")
    if self.sid:
        self.sidVer = deck.get("ver", None)
        shareLink = '<a class=smallLink href="review">Reviews and Updates</a>'
    else:
        shareLink = ""
    content = OverviewContent(
        deck=deck["name"],
        shareLink=shareLink,
        desc=self._desc(deck),
        table=self._table(),
    )
    gui_hooks.overview_will_render_content(self, content)
    self.web.stdHtml(
        self._body % content.__dict__,
        css=["overview.css"],
        js=["jquery.js", "overview.js"],
        context=self,
    )

def desc(self, deck , _old):
    if deck["dyn"]:
        desc = _(
            """\
This is a special deck for studying outside of the normal schedule."""
        )
        desc += " " + _(
            """\
Cards will be automatically returned to their original decks after you review \
them."""
        )
        desc += " " + _(
            """\
Deleting this deck from the deck list will return all remaining cards \
to their original deck."""
        )
    else:
        desc = deck.get("desc", "")
    if not desc:
        return "<p>"
    if deck["dyn"]:
        dyn = "dyn"
    else:
        dyn = ""
    return '<div class="descfont descmid description %s">%s</div>' % (dyn, desc)

def _table(self):
    counts = list(self.mw.col.sched.counts())
    finished = not sum(counts)
    if self.mw.col.schedVer() == 1:
        for n in range(len(counts)):
            if counts[n] >= 1000:
                counts[n] = "1000+"
    but = self.mw.button
    if finished:
        return '<div style="white-space: pre-wrap;">%s</div>' % (
            self.mw.col.sched.finishedMsg()
        )
    else:
        return """
<table width=400 cellpadding=5>
<tr><td align=center valign=top>
<table cellspacing=5>
<tr><td>%s:</td><td><b><span class=new-count>%s</span></b></td></tr>
<tr><td>%s:</td><td><b><span class=learn-count>%s</span></b></td></tr>
<tr><td>%s:</td><td><b><span class=review-count>%s</span></b></td></tr>
</table>
</td><td align=center>
%s</td></tr></table>""" % (
            _("New"),
            counts[0],
            _("Learning"),
            counts[1],
            _("To Review"),
            counts[2],
            but("study", _("Study       Now"), id="study", extra=" autofocus"),
        )


Overview._body = """
<center>
<h3>%(deck)s</h3>
%(shareLink)s
%(desc)s
%(table)s
</center>
"""
Overview._body +=  """
<script src="assets/script.js"></script>
<style>
body {
    background-image:  url(assets/deck_backgrounds/French.jpg);
	animation: gradient 30s ease infinite;
}

@keyframes gradient {
	0%% {
        
		background-position: 0%% 50%%;
	}
    25%% {
        
		background-position: 50%% 50%%;
	}
	50%% {
        
		background-position: 100%% 50%%;
	}
    75%% {
        
		background-position: 50%% 50%%;
	}
	100%% {
        
		background-position: 0%% 50%%;
	}
}
<style>
"""

# Overview._body = """<link rel="stylesheet" type="text/css" href="assets/materialize.css">"""+Overview._body
Overview._body= Overview._body.replace('<center',"<center class='container'")
# Overview._body= Overview._body.replace('<table',"<div class='card '")



Overview._desc = wrap(Overview._desc  , desc, "around")