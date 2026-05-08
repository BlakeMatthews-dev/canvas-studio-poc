import { BotanicalBranch, palette } from '../brand';
import './website.css';

/**
 * Canvas Studio marketing website.
 *
 * Ported from the Rooted & Revitalized design bundle's
 * "Canvas Studio Website.html". Voice rule: no em dashes.
 *
 * The original used a custom <image-slot> drop element for the hero
 * artwork; that's design-tool-specific and replaced here with a
 * styled placeholder. Wire to a real image when one exists.
 */
export function CanvasStudioWebsite() {
  return (
    <div className="canvas-studio-website">
      <Topbar />
      <Hero />
      <PipelineSection />
      <HonestBand />
      <FeaturesSection />
      <StatsBand />
      <QuoteBand />
      <ClosingBand />
      <Footer />
    </div>
  );
}

function Topbar() {
  return (
    <header className="topbar">
      <a href="#" className="mark">
        <span>Canvas Studio</span>
        <span className="script">by</span>
        <span>Rooted &amp; Revitalized</span>
      </a>
      <nav className="nav">
        <a href="#how">How it grows</a>
        <a href="#series">The series</a>
        <a href="#features">Features</a>
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
      width="120"
      height="120"
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
            <span className="eyebrow">A storybook studio for the people you love most</span>
          </div>
          <h1>
            <span className="caps">A storybook,</span>
            <span className="script">grown from</span>
            <span className="caps">your family memories.</span>
          </h1>
          <p className="lead">
            Canvas Studio takes the pictures you already love and grows them
            into a real, printed storybook, one page at a time. You stay
            close the whole way, choosing the art and adding the small
            touches only you would think of. Your tale unfolds from a handful
            of cherished photographs, through a storyboard, into a book you
            can read at bedtime.
          </p>
          <div className="meta-row">
            <a href="/app.html" className="btn-primary">Begin a book</a>
            <a href="#how" className="btn-ghost">See how it grows →</a>
          </div>
        </div>

        <div className="hero-art" aria-label="Sample book cover">
          <CornerSprig position="tl" />
          <CornerSprig position="br" />
          <div className="placeholder">
            A sample book cover lives here.
            <small>Drop in finished art when ready.</small>
          </div>
        </div>
      </div>
    </section>
  );
}

interface Stage {
  phase: string;
  title: string;
  script: string;
  body: string;
  aside: string;
}

const STAGES: Stage[] = [
  {
    phase: 'Phase 01',
    title: 'Story',
    script: 'drafting',
    body:
      "Tell us your idea, even half a sentence on a napkin will do. Our Story Conductor guides an ensemble of AI to compose your scenes, and you rename, reorder, or rewrite any of them before a single image is drawn.",
    aside: 'Your scenes arrive as a list you can rewrite. Nothing else stirs until you say go.',
  },
  {
    phase: 'Phase 02',
    title: 'Style',
    script: 'sampling',
    body:
      "Pick a feeling, watercolor, gouache, paper-cut, or soft pencil. We'll show you sample after sample until one feels like home. Every one you've ever liked is tucked away, never written over.",
    aside: 'Every sample stays right where you left it. Choose any of them, any time.',
  },
  {
    phase: 'Phase 03',
    title: 'Character',
    script: 'likeness',
    body:
      "Send us up to five photographs of your little one. The art treats them gently, holding onto their face, their hair, the particular shape of who they are, and dressing them up in the style you chose.",
    aside: "Your child's likeness is held with care, never reinvented.",
  },
  {
    phase: 'Phase 04',
    title: 'Storyboard',
    script: 'overview',
    body:
      "The whole book laid out at once, every scene a tiny picture, so you can feel the rhythm of it before any page is finished. Reshuffle if you'd like, or step straight into the pages themselves.",
    aside: 'The pacing of your whole story, visible in one quiet row.',
  },
  {
    phase: 'Phase 05',
    title: 'Pages',
    script: 'in layers',
    body:
      "Every page is built up like a paper-cut collage, the background, your little one, and the small props around them. Redo any part of it on its own and leave the rest exactly as you liked it. When you're happy, the picture quietly polishes itself.",
    aside: "Every drawing you've ever made is still here. Tap an old one to bring it home.",
  },
];

function PipelineSection() {
  return (
    <section className="band muted" id="how">
      <div className="wrap">
        <div className="section-head">
          <div className="eyebrow">How a story takes root</div>
          <h2>
            Five quiet steps. <span className="script">One book.</span>
          </h2>
          <p className="sub">
            Every step is yours to redo, undo, or rewrite. Nothing happens
            without your blessing. Your work tucks itself away every few
            seconds, all on its own, so your hands stay free for the
            important parts.
          </p>
        </div>

        <div className="pipeline">
          <div className="stem" aria-hidden />
          {STAGES.map((s, i) => (
            <div className="stage" key={s.phase}>
              <div className="stage-card">
                <span className="eyebrow">{s.phase}</span>
                <h3>
                  {s.title} <span className="script">{s.script}</span>
                </h3>
                <p>{s.body}</p>
              </div>
              <div className="stage-node">
                <div className="dot">{String(i + 1).padStart(2, '0')}</div>
              </div>
              <div className="stage-aside">{s.aside}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function HonestBand() {
  return (
    <section className="band" id="honest">
      <div className="wrap" style={{ maxWidth: 880, textAlign: 'center' }}>
        <div className="section-head" style={{ marginBottom: 32 }}>
          <div className="eyebrow">Honest about the magic</div>
          <h2>
            How we <span className="script">do it.</span>
          </h2>
        </div>
        <p className="honest-quote">
          We'll be honest. There is software in here, and ours is led by an
          AI Engineer in Residence who's worked deep inside the AI world and
          the studios behind some of the most beloved children's stories
          ever told. Our <em>Story Conductor</em> guides an ensemble of AI to
          compose your tale like magic, and you finish it in your own voice,
          with the touch that makes every book a perfect symphony of{' '}
          <span className="script-trio">love, magic, and family</span>.
        </p>
      </div>
    </section>
  );
}

interface Feature {
  num: string;
  title: string;
  body: string;
  leafColor: string;
}

const FEATURES: Feature[] = [
  {
    num: 'i.',
    title: 'They look like themselves',
    body:
      'Up to five photographs guide every drawing of your little one. If the art ever wanders too far from their face, we gently bring them back to the child you sent us. They will always look like themselves.',
    leafColor: palette.sage[500],
  },
  {
    num: 'ii.',
    title: 'Nothing is ever thrown away',
    body:
      "Every drawing you've ever liked is still here, just behind the one on screen. Tap a thumbnail and that older version comes home, exactly as it was. Nothing you've made disappears.",
    leafColor: palette.clay[500],
  },
  {
    num: 'iii.',
    title: 'It saves itself, without asking',
    body:
      'Your book tucks itself away every few seconds, all on its own. Close the tab, lose the wifi, hop to another room with the iPad. When you come back, nothing has gone missing, not a single line.',
    leafColor: palette.sage[500],
  },
];

function LeafBg({ color }: { color: string }) {
  return (
    <svg className="leaf-bg" width="160" height="160" viewBox="0 0 100 100" fill={color} aria-hidden>
      <path d="M50,5 C70,5 92,20 92,50 C92,78 72,94 50,95 C50,95 50,65 36,52 C22,39 8,35 8,50 C8,22 30,5 50,5 Z" />
    </svg>
  );
}

function FeaturesSection() {
  return (
    <section className="band" id="features">
      <div className="wrap">
        <div className="section-head">
          <div className="eyebrow">What we tend to</div>
          <h2>
            Small things, <span className="script">looked after carefully.</span>
          </h2>
          <p className="sub">
            Three little promises we make, that turn a quick novelty into a
            book you'll actually wrap and give.
          </p>
        </div>

        <div className="feature-grid">
          {FEATURES.map((f) => (
            <article className="feature" key={f.num}>
              <LeafBg color={f.leafColor} />
              <div className="num">{f.num}</div>
              <h3>{f.title}</h3>
              <p>{f.body}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

interface Stat {
  num: React.ReactNode;
  script: string;
  label: string;
}

const STATS: Stat[] = [
  { num: <>5<span className="small">photos</span></>, script: 'to teach the art', label: "your little one's face" },
  { num: '∞', script: 'do-overs, always', label: 'every drawing kept' },
  { num: <>3<span className="small">sec</span></>, script: 'between quiet saves', label: 'your work, tucked away' },
  { num: '1', script: 'family at a time', label: 'your book, only yours' },
];

function StatsBand() {
  return (
    <section className="band dark">
      <div className="wrap">
        <div className="section-head">
          <div className="eyebrow">Small reassurances</div>
          <h2>
            The promises <span className="script">we keep.</span>
          </h2>
        </div>
        <div className="stats">
          {STATS.map((s, i) => (
            <div className="stat" key={i}>
              <div className="num">{s.num}</div>
              <div className="script">{s.script}</div>
              <div className="label">{s.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function QuoteBand() {
  return (
    <section className="band">
      <div className="wrap quote-band">
        <div className="quote-mark">&ldquo;</div>
        <blockquote className="q">
          It never once asked us to throw something away. Every drawing we'd
          ever loved was still tucked behind the one on screen, waiting if we
          wanted it back.
        </blockquote>
        <div className="q-source">From the studio's notes</div>
      </div>
    </section>
  );
}

function ClosingBand() {
  return (
    <section className="band muted" id="start">
      <div className="wrap closing">
        <div className="section-head" style={{ marginBottom: 24 }}>
          <div className="eyebrow">Begin</div>
        </div>
        <h2>
          Plant the first <span className="script">page.</span>
        </h2>
        <p className="lead">
          A new storybook begins with the people you love most, a story you
          already know by heart, and a look that feels like home. The rest
          grows quietly alongside you.
        </p>
        <a href="/app.html" className="btn-primary">Open Canvas Studio</a>
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
            <div className="foot-mark">Canvas Studio</div>
            <div className="foot-script">a Rooted &amp; Revitalized atelier</div>
            <p className="blurb">
              A small studio for slow, careful, family storybooks. Made with
              patience, and a great deal of love.
            </p>
          </div>
          <div>
            <h4>The journey</h4>
            <ul>
              <li><a href="#how">Story drafting</a></li>
              <li><a href="#how">Style sampling</a></li>
              <li><a href="#how">Character likeness</a></li>
              <li><a href="#how">Storyboard</a></li>
              <li><a href="#how">Pages</a></li>
            </ul>
          </div>
          <div>
            <h4>Studio</h4>
            <ul>
              <li><a href="#">Spec</a></li>
              <li><a href="#">Changelog</a></li>
              <li><a href="#">Pricing</a></li>
              <li><a href="#">FAQ</a></li>
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
          <div>© 2026 Canvas Studio · Rooted &amp; Revitalized.</div>
          <div className="with-care">with care, with patience.</div>
        </div>
      </div>
    </footer>
  );
}
