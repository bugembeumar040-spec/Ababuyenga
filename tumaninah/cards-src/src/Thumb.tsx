import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import {useFonts} from './fonts';

const CREAM = '#F2EDE2';
const OCHRE = '#E0A94F';
const SIENNA = '#C4633B';
const SLATE = '#8A8F9A';
const INK = '#141A2A';

// Reverse-engineered from what vidIQ's own thumbnails do, then rebuilt in this
// pack's palette. Four rules carry over: two elements and no more, type in one
// zone at roughly half the frame, a two-colour hierarchy where the payoff word
// is the largest thing, and a dark ground so both the type and the subject pop.
//
// One device carries over almost unchanged, because here it happens to be true:
// vidIQ strikes through the bad advice. The whole argument of this video is that
// "peace" is the wrong word for ṭumaʾnīnah — so the strike-through is not a
// borrowed gimmick, it is the thesis.
//
// What deliberately does not carry over is the neon-and-highlighter register.
// On a Qurʾānic word study it would read as clickbait and misrepresent the film.
export const Thumb: React.FC<{
	src: string; ar: string; struck: string; payoff: string; ref: string; refBig: string;
	shiftX?: string; zoom?: string; wash?: number;
}> = ({src, ar, struck, payoff, ref, refBig, shiftX = '34%', zoom = '104%', wash = 0.14}) => {
	useFonts();
	return (
		<AbsoluteFill style={{backgroundColor: INK}}>
			<Img
				src={staticFile(src)}
				// A Flow image generated to this brief already has its subject right and
				// its left side dark, so it needs no shift. The pack frames were shot
				// centre and do.
				style={{position: 'absolute', width: zoom, height: zoom,
					left: shiftX, top: '-2%', objectFit: 'cover'}}
			/>
			{/* Deepen the whole frame, then black out the type side. The pack art is
			    pale by design; at 210px wide that pallor is what kills it. */}
			<AbsoluteFill style={{backgroundColor: INK, opacity: wash}} />
			<AbsoluteFill
				style={{
					background: `linear-gradient(to right, ${INK} 0%, ${INK} 40%,` +
						` rgba(20,26,42,0.86) 55%, rgba(20,26,42,0) 80%)`,
				}}
			/>
			<AbsoluteFill style={{justifyContent: 'center', padding: '0 0 0 72px'}}>
				<div style={{display: 'flex', flexDirection: 'column', alignItems: 'flex-start'}}>
					<div dir="rtl" lang="ar" style={{
						fontFamily: 'Amiri', fontWeight: 700, fontSize: 96, lineHeight: 1.15,
						color: CREAM, whiteSpace: 'nowrap', marginBottom: 62,
					}}>{ar}</div>

					{/* the verdict, in one glance */}
					<div style={{position: 'relative', display: 'inline-block', marginBottom: 4}}>
						<div style={{fontFamily: 'Inter', fontWeight: 700, fontSize: 76,
							lineHeight: 1.0, color: SLATE, letterSpacing: -1}}>{struck}</div>
						<div style={{position: 'absolute', left: -10, right: -10, top: '52%',
							height: 11, backgroundColor: SIENNA, borderRadius: 6,
							transform: 'rotate(-2.5deg)'}} />
					</div>

					<div style={{fontFamily: 'Inter', fontWeight: 700, fontSize: 122,
						lineHeight: 1.0, color: OCHRE, letterSpacing: -2, marginTop: 10}}>{payoff}</div>

					<div style={{display: 'flex', alignItems: 'baseline', gap: 12, marginTop: 30}}>
						<span style={{fontFamily: 'Inter', fontWeight: 700, fontSize: 30,
							letterSpacing: 4, color: CREAM, opacity: 0.72}}>{ref}</span>
						<span style={{fontFamily: 'Inter', fontWeight: 700, fontSize: 54,
							color: OCHRE, letterSpacing: -1}}>{refBig}</span>
					</div>
				</div>
			</AbsoluteFill>
		</AbsoluteFill>
	);
};
