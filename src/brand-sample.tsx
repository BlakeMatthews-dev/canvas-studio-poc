import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { MantineProvider, Button, TextInput, Card, Badge, Stack, Group } from '@mantine/core';

import './brand/tokens.css';
import '@mantine/core/styles.css';

import {
  brandTheme,
  Wordmark,
  TaglineRow,
  CategoryPill,
  Sprig,
  Sparkle,
  Leaf,
  HeartGlyph,
  BotanicalBranch,
  DividerSprig,
  WatercolorWash,
  TornPaper,
  PaperCard,
  palette,
  fonts,
  tracking,
  tagline,
  categories,
} from './brand';

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section style={{ marginBottom: 48 }}>
      <div
        style={{
          fontFamily: fonts.body,
          fontSize: 11,
          letterSpacing: tracking.widest,
          textTransform: 'uppercase',
          color: palette.sage[500],
          marginBottom: 16,
          fontWeight: 600,
        }}
      >
        {title}
      </div>
      {children}
    </section>
  );
}

function Swatch({ name, value }: { name: string; value: string }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', borderRadius: 12, overflow: 'hidden', border: '1px solid rgba(0,0,0,0.06)', minWidth: 120 }}>
      <div style={{ height: 56, background: value }} />
      <div style={{ padding: '8px 10px', background: palette.cream[50], fontFamily: fonts.body }}>
        <div style={{ fontSize: 12, color: palette.ink[900], fontWeight: 600 }}>{name}</div>
        <div style={{ fontSize: 10.5, color: palette.ink[500], fontFamily: 'ui-monospace, SF Mono, monospace' }}>
          {value}
        </div>
      </div>
    </div>
  );
}

function BrandSample() {
  return (
    <MantineProvider theme={brandTheme} cssVariablesSelector="#brand-root">
      <div className="rr" id="brand-root-inner" style={{ minHeight: '100vh', padding: '40px 48px' }}>
        <header style={{ marginBottom: 56, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
          <Sprig leafCount={9} size={48} />
          <Wordmark scale={1.4} />
          <TaglineRow />
          <CategoryPill />
        </header>

        <Section title="Palette · Sage">
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {(['50','100','200','300','400','500','600','700'] as const).map((k) => (
              <Swatch key={k} name={`sage ${k}`} value={palette.sage[k]} />
            ))}
          </div>
        </Section>

        <Section title="Palette · Cream / Clay / Ink">
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {(['50','100','200','300'] as const).map((k) => (
              <Swatch key={`cream-${k}`} name={`cream ${k}`} value={palette.cream[k]} />
            ))}
            {(['100','300','500'] as const).map((k) => (
              <Swatch key={`clay-${k}`} name={`clay ${k}`} value={palette.clay[k]} />
            ))}
            {(['100','300','500','700','900'] as const).map((k) => (
              <Swatch key={`ink-${k}`} name={`ink ${k}`} value={palette.ink[k]} />
            ))}
          </div>
        </Section>

        <Section title="Signal">
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <Swatch name="bloom" value={palette.signal.bloom} />
            <Swatch name="leaf" value={palette.signal.leaf} />
            <Swatch name="honey" value={palette.signal.honey} />
            <Swatch name="rust" value={palette.signal.rust} />
          </div>
        </Section>

        <Section title="Type">
          <div className="rr" style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <h1 className="rr-h1">A Quiet Garden Room</h1>
            <h2 className="rr-h2">Slow Saturdays, Soft Light</h2>
            <h3 className="rr-h3">Pothos in the Window</h3>
            <p className="rr-lead">
              Cut just below a node, find a sunny window, and wait. Roots take a few weeks, and patience is part of the point.
            </p>
            <div className="rr-eyebrow">Plant care · 5 min read</div>
            <div className="rr-label">Field journal</div>
            <div>
              <span className="rr-script-accent">handmade</span>{' '}
              <span style={{ fontFamily: fonts.body, color: palette.ink[700] }}>and well-considered.</span>
            </div>
          </div>
        </Section>

        <Section title="Brand primitives">
          <div style={{ display: 'flex', gap: 32, alignItems: 'center', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, alignItems: 'center' }}>
              <Sparkle size={32} />
              <div style={{ fontSize: 10, color: palette.ink[500], textTransform: 'uppercase', letterSpacing: tracking.wider }}>Sparkle</div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, alignItems: 'center' }}>
              <HeartGlyph size={28} />
              <div style={{ fontSize: 10, color: palette.ink[500], textTransform: 'uppercase', letterSpacing: tracking.wider }}>Heart</div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, alignItems: 'center' }}>
              <Leaf size={48} />
              <div style={{ fontSize: 10, color: palette.ink[500], textTransform: 'uppercase', letterSpacing: tracking.wider }}>Leaf</div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, alignItems: 'center' }}>
              <Sprig leafCount={6} size={56} />
              <div style={{ fontSize: 10, color: palette.ink[500], textTransform: 'uppercase', letterSpacing: tracking.wider }}>Sprig · 6</div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, alignItems: 'center' }}>
              <Sprig leafCount={12} size={56} />
              <div style={{ fontSize: 10, color: palette.ink[500], textTransform: 'uppercase', letterSpacing: tracking.wider }}>Sprig · 12</div>
            </div>
          </div>
          <div style={{ marginTop: 24 }}>
            <BotanicalBranch width={520} height={140} />
          </div>
          <div style={{ marginTop: 16, maxWidth: 520 }}>
            <DividerSprig />
          </div>
        </Section>

        <Section title="Motifs">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 18 }}>
            <PaperCard>
              <div className="rr-label" style={{ marginBottom: 8 }}>Paper card</div>
              <div className="rr-lead">Cream ground, soft paper shadow, rounded corners.</div>
            </PaperCard>
            <WatercolorWash style={{ height: 160, borderRadius: 12, overflow: 'hidden', background: palette.cream[100] }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', fontFamily: fonts.script, fontSize: 48, color: palette.sage[600] }}>
                watercolor
              </div>
            </WatercolorWash>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', background: palette.sage[100] }}>
              <TornPaper>
                <div style={{ fontFamily: fonts.display, fontSize: 22, color: palette.sage[600], textTransform: 'uppercase', fontWeight: 600 }}>
                  Torn paper
                </div>
              </TornPaper>
            </div>
          </div>
        </Section>

        <Section title="Mantine components themed">
          <Card withBorder>
            <Stack gap="md">
              <Group>
                <Button>Follow along</Button>
                <Button variant="light">Save project</Button>
                <Button variant="outline">Read more</Button>
                <Button variant="subtle">Cancel</Button>
              </Group>
              <Group>
                <Button size="xs">Small</Button>
                <Button size="lg">Large primary</Button>
                <Button disabled>Disabled</Button>
              </Group>
              <TextInput label="Your name" placeholder="First name" />
              <TextInput label="Email" placeholder="hello@garden.home" />
              <Group>
                <Badge color="sage">Plant care</Badge>
                <Badge color="sage" variant="light">#propagation</Badge>
                <Badge color="clay">DIY</Badge>
                <Badge color="sage" variant="outline">New</Badge>
              </Group>
            </Stack>
          </Card>
        </Section>

        <Section title="Voice">
          <PaperCard>
            <div style={{ fontFamily: fonts.body, color: palette.ink[700], fontSize: 14, lineHeight: 1.6 }}>
              <strong style={{ color: palette.sage[600] }}>{tagline.primary}</strong>
              {' · '}
              <strong style={{ color: palette.sage[600] }}>{tagline.secondary}</strong>
              <div style={{ marginTop: 8, fontStyle: 'italic', color: palette.ink[500] }}>
                Categories: {categories.join(', ')}.
              </div>
              <div style={{ marginTop: 8 }}>
                Rule: no em dashes. Use commas, periods, or " and ".
              </div>
            </div>
          </PaperCard>
        </Section>

        <footer style={{ marginTop: 64, color: palette.ink[300], fontSize: 12, textAlign: 'center' }}>
          Brand sample · ported from the Rooted &amp; Revitalized design system.
        </footer>
      </div>
    </MantineProvider>
  );
}

createRoot(document.getElementById('brand-root')!).render(
  <StrictMode>
    <BrandSample />
  </StrictMode>,
);
