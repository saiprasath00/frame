import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from sync_links import parse_markdown,parse_website,merge_sources,clean_url,make_entry

MARKDOWN = '''
# ► Streaming Sites
## ▷ Stream Aggregators
* 🌟 **[Cinema One](https://cinema-one.example/)** - 4K / Dual Audio
* **[1080 Stream](https://not4k.example/)** - 1080p / Sub
* [Another 4K](https://another4k.example/) or [Second Cinema](https://second-cinema.example/) - 4K / Movies
## ▷ Anime Streaming
* 🌐 [Anime Index](https://index.example/) - Anime Site Index
* ⭐ **[Fresh Anime](https://anime.example/)** - Sub / Dub
# ► Download Sites
* ⭐ **[Rentry Forward](https://rentry.co/FMHYB64#defe)** - Movies / 4K
* ⭐ **[VegaMovies](https://old-movies.example/)** - Movies / 4K
* **[Some other](https://other.example/)** - Movies / TV
* [Movie Site](https://movies.example/) / [Telegram](https://t.me/movie_site) - Movies
## ▷ Telegram Channels
* [Group](https://group.example/) - Movies
## ▷ Anime Downloading
* ⭐ **[Tokyo Insider](https://tokyo.example/)** - Sub / Dub
* 🌐 [Directory](https://directory.example/) - Anime Download Index
# ► Streaming Apps
* [Not a Site](https://app.example/) - Streaming App
'''
HTML = '''<main><div class="vp-doc">
<h2>Streaming Sites</h2><h3>Stream Aggregators</h3><ul>
<li><a href="https://cinema-new.example/">Cinema One</a> - 4K / Dual Audio</li>
</ul><h3>Anime Streaming</h3><ul><li><a href="https://anime.example/">Fresh Anime</a> - Sub / Dub</li></ul>
<h2>Download Sites</h2><ul><li><a href="https://new-movies.example/">VegaMovies</a> - Movies / TV</li>
<li><a href="https://rentry.co/abcd#base64">Encoded</a> - Movies</li></ul>
<h3>Anime Downloading</h3><ul><li><a href="https://tokyo.example/">Tokyo Insider</a> - Sub</li></ul>
</div></main>'''

class TestSync(unittest.TestCase):
    def test_parses_sections(self):
        entries=parse_markdown(MARKDOWN)
        names={x[0]:x[2] for x in entries}
        self.assertEqual(names['VegaMovies'],'movies')
        self.assertEqual(names['Cinema One'],'fourk')
        self.assertEqual(names['Second Cinema'],'fourk')
        self.assertEqual(names['Fresh Anime'],'anime')
        self.assertEqual(names['Tokyo Insider'],'anidownload')
        for bad in ('Rentry Forward','Directory','Anime Index','Group','Not a Site','1080 Stream'):
            self.assertNotIn(bad,names)
        self.assertEqual(len(entries),8)
    def test_html(self):
        names={x[0]:x[1] for x in parse_website(HTML)}
        self.assertEqual(names['VegaMovies'],'https://new-movies.example/')
        self.assertEqual(names['Cinema One'],'https://cinema-new.example/')
        self.assertNotIn('Encoded',names)
    def test_domain_change_favors_changed_source(self):
        old=[('VegaMovies','https://old-movies.example/','movies')]
        repo=[('VegaMovies','https://old-movies.example/','movies')]
        site=[('VegaMovies','https://new-movies.example/','movies')]
        self.assertEqual(merge_sources(repo,site,old)[0][1], 'https://new-movies.example/')
        self.assertEqual(merge_sources(site,repo,old)[0][1], 'https://new-movies.example/')
    def test_block_indirect(self):
        for url in ('https://rentry.co/whatever','https://paste.to/paste',
                    'https://github.com/owner/repo','http://good.example',
                    'https://good.example/#base64', 'javascript:alert(1)',
                    'https://t.me/whatever'):
            self.assertIsNone(clean_url(url))
        self.assertIsNotNone(make_entry('HD films','https://films.example/movies','movies'))

if __name__ == '__main__': unittest.main()
