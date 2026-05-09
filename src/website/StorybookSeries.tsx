import { BotanicalBranch, palette } from '../brand';
import './storybook-series.css';

/**
 * Storybook Series marketing page.
 *
 * Ported from the Rooted & Revitalized design bundle's
 * "Storybook Series Website.html". Sibling page to the Canvas Studio
 * marketing site (CanvasStudioWebsite.tsx) — same brand, different
 * product surface (curated, ready-before-bedtime books with limited
 * personalization vs. the full Canvas Studio custom build).
 *
 * Voice rule: no em dashes.
 */
export function StorybookSeries() {
  return (
    <div className="storybook-series-website">
      <Topbar />
      <Hero />
      <DifferenceSection />
      <FeaturedBook />
      <PersonaSection />
      <ComingNextSection />
      <ClosingBand />
      <Footer />
    </div>
  );
}

function Topbar() {
  return (
    <header className="topbar">
      <a href="/" className="mark">
        <span>Main Character Crew</span>
        <span className="script">by</span>
        <span>Rooted &amp; Revitalized</span>
      </a>
      <nav className="nav">
        <a href="/">Custom books</a>
        <a href="/storybook-series.html" className="active">The series</a>
        <a href="#how">How it works</a>
        <a href="#pricing">Pricing</a>
      </nav>
      <a href="/app.html" className="cta">Begin a book</a>
    </header>
  );
}

function CornerSprig({ position }: { position: 'tl' | 'br' }) {
  return (
    <svg
      className={`corner-spr ${position}`}
      viewBox="0 0 100 100"
      fill={palette.sage[300]}
      aria-hidden
    >
      <path d="M50,5 C70,5 92,20 92,50 C92,78 72,94 50,95 C50,95 50,65 36,52 C22,39 8,35 8,50 C8,22 30,5 50,5 Z" />
    </svg>
  );
}

function Hero() {
  return (
    <section className="hero">
      <div className="wash" />
      <div className="wrap hero-inner">
        <div>
          <div className="eyebrow-row">
            <span className="rule" />
            <span className="eyebrow">A storybook series, ready before bedtime</span>
          </div>
          <h1>
            <span className="caps">Stories for</span>
            <span className="script">the days</span>
            <span className="caps">that ask the most.</span>
          </h1>
          <p className="lead">
            Some books, you grow from scratch. These ones are different. The
            story is already written, gently, by people who know how big a
            child's feelings can get. You add your little one's face, the
            fidget that lives in their pocket, the headphones they wear when
            the world gets too loud, and the book is theirs by the end of
            the afternoon.
          </p>
          <div className="meta-row">
            <a href="/app.html" className="btn-primary">Make their first book</a>
            <a href="#featured" className="btn-ghost">Read a sample →</a>
          </div>
        </div>

        {/* Hero book stack */}
        <div className="book-stack" aria-label="Stack of two storybooks">
          <CornerSprig position="tl" />
          <CornerSprig position="br" />
          <div className="book b1">
            <div className="spine" />
          </div>
          <div className="book b2">
            <div className="spine" />
            <div className="placeholder">A sample cover lives here.</div>
          </div>
        </div>
      </div>
    </section>
  );
}

interface Difference {
  icon: React.ReactNode;
  title: string;
  script: string;
  body: string;
}

const DIFFS: Difference[] = [
  {
    icon: (
      <svg width="46" height="46" viewBox="0 0 100 100" fill={palette.sage[500]}>
        <path d="M20,12 L80,12 L80,82 C80,86 76,90 72,90 L28,90 C24,90 20,86 20,82 Z M28,18 L28,80 C28,82 30,84 32,84 L68,84 C70,84 72,82 72,80 L72,18 Z" />
        <rect x="34" y="32" width="32" height="3" />
        <rect x="34" y="44" width="32" height="3" />
        <rect x="34" y="56" width="22" height="3" />
      </svg>
    ),
    title: 'We wrote the',
    script: 'story',
    body:
      "Each book is hand-written for one big feeling. You don't need a premise, or a plot, or an ending. Just bring your child.",
  },
  {
    icon: (
      <svg width="46" height="46" viewBox="0 0 100 100" fill={palette.sage[500]}>
        <path d="M50,16 C58,16 64,22 64,30 C64,38 58,44 50,44 C42,44 36,38 36,30 C36,22 42,16 50,16 Z M22,86 C22,68 34,56 50,56 C66,56 78,68 78,86 Z" />
      </svg>
    ),
    title: 'You bring the',
    script: 'heart',
    body:
      "Their face, their hair, their favorite fidget, the headphones they wear when the world is too loud. Every page is shaped around the child you know.",
  },
  {
    icon: (
      <svg width="46" height="46" viewBox="0 0 100 100" fill={palette.sage[500]}>
        <path d="M50,12 C71,12 88,29 88,50 C88,71 71,88 50,88 C29,88 12,71 12,50 C12,29 29,12 50,12 Z M50,20 C33,20 20,33 20,50 C20,67 33,80 50,80 C67,80 80,67 80,50 C80,33 67,20 50,20 Z" />
        <path d="M50,28 L50,52 L66,62 L62,68 L44,56 L44,28 Z" />
      </svg>
    ),
    title: 'Ready before',
    script: 'bedtime',
    body:
      "No pages-by-layer studio work. No long evening of choosing. The finished book lands in your hands in minutes, not weeks.",
  },
];

function DifferenceSection() {
  return (
    <section className="band muted" id="how">
      <div className="wrap">
        <div className="section-head">
          <div className="eyebrow">How these are different</div>
          <h2>
            You don't write a word. <span className="script">They still belong to you.</span>
          </h2>
          <p className="sub">
            Different from our custom storybooks, and meant to be. The hard
            creative work is already done, so the tender, personal part is
            all that's left.
          </p>
        </div>

        <div className="diff-grid">
          {DIFFS.map((d) => (
            <article className="diff" key={d.script}>
              <div className="icon-wrap">{d.icon}</div>
              <h3>
                {d.title} <span className="script">{d.script}</span>
              </h3>
              <p>{d.body}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

function FeaturedBook() {
  return (
    <section className="band" id="featured">
      <div className="wrap featured-inner">
        <div className="featured-cover" aria-label="Featured book: Calm Down Donuts">
          <div className="spine" />
          <div className="placeholder">Cover illustration goes here.</div>
          <div className="cover-text">
            <div className="their">Maya &amp; the</div>
            <div className="title">
              Calm Down<br />Donuts
            </div>
          </div>
        </div>

        <div className="featured-content">
          <div className="eyebrow">First in the series</div>
          <h2>
            <span className="their-name">Their name</span> &amp; the<br />
            Calm Down Donuts
          </h2>
          <div className="subtitle">A story for when feelings are too big.</div>

          <p>
            The donut shop is supposed to be the best part of the day. But
            the line is long, the music is loud, and someone took the last
            chocolate one. Your little one's chest is starting to feel like
            a balloon that's just about full.
          </p>
          <p>
            Then a kindly baker, a dog with a bow tie, and four very strange
            donuts (one of them is teaching everyone how to breathe) help
            them find their way back to themselves, one nibble at a time.
          </p>
          <p>
            The donuts in this book are not real. The breathing is. So is
            the squeeze your little one will give themselves on page nine.
          </p>

          <div className="for-the-moments">
            <div className="label-line">For the moments when</div>
            <ul>
              <li>their feelings get too big to hold</li>
              <li>the place is too loud, too bright, too much</li>
              <li>the thing they wanted is gone</li>
              <li>they need a pocketful of small, gentle tools</li>
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}

interface Persona {
  num: string;
  label: string;
  title: string;
  script: string;
  body: string;
}

const PERSONAS: Persona[] = [
  {
    num: '01',
    label: 'The basics',
    title: 'Their name &',
    script: 'their face',
    body:
      'Up to five photographs and the name they answer to. We hold all of it gently, and never let the art forget who they are.',
  },
  {
    num: '02',
    label: 'The look of them',
    title: 'Hair, skin,',
    script: 'eyes, smile',
    body:
      "The particular brown of their hair on a sunny day. The gap where a tooth used to be. The freckles you've counted at least twice.",
  },
  {
    num: '03',
    label: 'Comfort tools',
    title: 'The fidget in',
    script: 'their pocket',
    body:
      'The fidget toy, the chewy necklace, the worry stone. The thing they reach for first. It rides along on every page, right where it belongs.',
  },
  {
    num: '04',
    label: 'The world, dialed down',
    title: 'Headphones,',
    script: 'soft clothes, bare feet',
    body:
      'Noise-cancelling headphones, the only shirt without a tag, the shoes that are never on. The art respects the way they meet a loud world.',
  },
  {
    num: '05',
    label: 'How they speak',
    title: 'Words, signs,',
    script: 'a tablet',
    body:
      "An AAC tablet, sign language, a few favorite words on repeat, or a quiet kind of confidence. Whatever your child's voice looks like, it shows up on the page.",
  },
  {
    num: '06',
    label: 'Their favorite of everything',
    title: 'Their color,',
    script: 'their creature',
    body:
      "The color they cannot get enough of. The animal that's been the favorite for nine months running. We work both into the story like Easter eggs you'll spot on every reread.",
  },
];

function PersonaSection() {
  return (
    <section className="band muted">
      <div className="wrap">
        <div className="section-head">
          <div className="eyebrow">Make them, them</div>
          <h2>
            The little things <span className="script">that make all the difference.</span>
          </h2>
          <p className="sub">
            We ask for these so the child on the page is unmistakably yours,
            right down to the headphones in their backpack.
          </p>
        </div>

        <div className="persona-grid">
          {PERSONAS.map((p) => (
            <div className="persona-card" key={p.num}>
              <div className="label-line">
                {p.num} · {p.label}
              </div>
              <h4>
                {p.title} <span className="script">{p.script}</span>
              </h4>
              <p>{p.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

interface Upcoming {
  season: string;
  title: string;
  forText: string;
  leafColor: string;
}

const UPCOMING: Upcoming[] = [
  { season: 'Soon · Spring', title: 'Whisper\nGarden', forText: 'for when the world feels too loud', leafColor: palette.sage[300] },
  { season: 'Soon · Summer', title: 'Borrow\nBox', forText: 'for when sharing feels hard', leafColor: palette.clay[300] },
  { season: 'Soon · Autumn', title: 'Big Bird\nWords', forText: "for when the words won't come out", leafColor: palette.sage[300] },
  { season: 'Soon · Winter', title: 'In-Between\nBench', forText: 'for when making friends takes a minute', leafColor: palette.clay[300] },
];

function LeafOrnament({ color }: { color: string }) {
  return (
    <svg className="leaf" width="120" height="120" viewBox="0 0 100 100" fill={color} aria-hidden>
      <path d="M50,5 C70,5 92,20 92,50 C92,78 72,94 50,95 C50,95 50,65 36,52 C22,39 8,35 8,50 C8,22 30,5 50,5 Z" />
    </svg>
  );
}

function ComingNextSection() {
  return (
    <section className="band">
      <div className="wrap">
        <div className="section-head">
          <div className="eyebrow">Coming next, gently</div>
          <h2>
            More stories <span className="script">on their way.</span>
          </h2>
          <p className="sub">
            One new title at a time, written slowly and tested with real
            families before they reach yours.
          </p>
        </div>

        <div className="shelf">
          {UPCOMING.map((u) => {
            const [line1, line2] = u.title.split('\n');
            return (
              <div className="upcoming" key={u.title}>
                <div className="small-label">{u.season}</div>
                <div>
                  <div className="their">Their name &amp; the</div>
                  <h4>
                    {line1}
                    <br />
                    {line2}
                  </h4>
                </div>
                <div className="for">{u.forText}</div>
                <LeafOrnament color={u.leafColor} />
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function ClosingBand() {
  return (
    <section className="band dark" id="start">
      <div className="wrap closing">
        <div className="section-head" style={{ marginBottom: 24 }}>
          <div className="eyebrow">Begin</div>
        </div>
        <h2>
          Make their first <span className="script">storybook.</span>
        </h2>
        <p className="lead">
          A few photographs, the things that help them feel safe, and a
          story already waiting for them. The book lands in your hands
          before bedtime.
        </p>
        <a href="/app.html" className="btn-primary on-dark">Open the studio</a>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="foot">
      <div className="wrap">
        <div className="foot-inner">
          <div>
            <div className="foot-mark">Main Character Crew</div>
            <div className="foot-script">a Rooted &amp; Revitalized atelier</div>
            <p className="blurb">
              A small studio for slow, careful, family storybooks. Made with
              patience, and a great deal of love.
            </p>
          </div>
          <div>
            <h4>The studio</h4>
            <ul>
              <li><a href="/">Custom books</a></li>
              <li><a href="/storybook-series.html">The series</a></li>
              <li><a href="#how">How it works</a></li>
              <li><a href="#">Pricing</a></li>
            </ul>
          </div>
          <div>
            <h4>The series</h4>
            <ul>
              <li><a href="#featured">Calm Down Donuts</a></li>
              <li><a href="#">Whisper Garden</a></li>
              <li><a href="#">Borrow Box</a></li>
              <li><a href="#">Big Bird Words</a></li>
            </ul>
          </div>
          <div>
            <h4>Beneath</h4>
            <ul>
              <li><a href="#">Privacy</a></li>
              <li><a href="#">Terms</a></li>
              <li><a href="#">Acknowledgments</a></li>
              <li><a href="#">Contact</a></li>
            </ul>
          </div>
        </div>

        <div className="foot-ornament">
          <BotanicalBranch width={320} height={60} color={palette.sage[300]} />
        </div>

        <div className="foot-bot">
          <div>© 2026 Main Character Crew · Rooted &amp; Revitalized.</div>
          <div className="with-care">with care, with patience.</div>
        </div>
      </div>
    </footer>
  );
}
