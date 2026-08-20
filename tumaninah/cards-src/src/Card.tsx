import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {useFonts} from './fonts';

export type CardProps = {
	ch: string;
	ar: string;
	head: string;
	sub: string;
	bg: string;
};

const INDIGO = '#2E3A56';
const OCHRE = '#C89A4A';
const OCHRE_LIGHT = '#E8C98A';
const SLATE = '#6B7280';
const SIENNA = '#A65A3A';
const CREAM = '242, 237, 226';

// Long āyah fragments need to give back the room a single word can afford.
// Measured on base letters: harakāt are stacked marks and take no extra width,
// so counting them would shrink a short fully-vocalised word for no reason.
const arabicSize = (ar: string) => {
	const n = ar.replace(/[\u064B-\u0652\u0670\u06D6-\u06ED]/g, '').length;
	if (n <= 10) return 116;
	if (n <= 18) return 92;
	if (n <= 30) return 72;
	return 56;
};

export const Card: React.FC<CardProps> = ({ch, ar, head, sub, bg}) => {
	useFonts();
	const frame = useCurrentFrame();
	const {durationInFrames} = useVideoConfig();

	// Each element rises into place, and the whole card fades out at the tail so
	// it can be dropped on the timeline without hand-keying an exit.
	const rise = (start: number) => {
		const p = interpolate(frame, [start, start + 16], [0, 1], {
			extrapolateLeft: 'clamp',
			extrapolateRight: 'clamp',
		});
		const eased = 1 - Math.pow(1 - p, 3);
		return {opacity: eased, transform: `translateY(${(1 - eased) * 26}px)`};
	};

	const out = interpolate(
		frame,
		[durationInFrames - 14, durationInFrames - 1],
		[1, 0],
		{extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
	);

	const ruleGrow = interpolate(frame, [0, 22], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});

	return (
		<AbsoluteFill style={{backgroundColor: bg, opacity: out}}>
			{/* The art behind these cards runs from bare paper to near-black storm, so
			    indigo type alone is not readable everywhere. A feathered cream wash
			    rising off the bottom edge restores contrast without reading as a box —
			    it carries in the alpha, so the WebM is legible over any frame. */}
			<AbsoluteFill
				style={{
					opacity: interpolate(frame, [0, 18], [0, 1], {
						extrapolateLeft: 'clamp',
						extrapolateRight: 'clamp',
					}),
					background:
						`linear-gradient(to top, rgba(${CREAM},0.80) 0%, rgba(${CREAM},0.66) 30%,` +
						` rgba(${CREAM},0.32) 60%, rgba(${CREAM},0) 100%)`,
					top: 'auto',
					height: 430,
				}}
			/>
			<AbsoluteFill
				style={{
					justifyContent: 'flex-end',
					alignItems: 'flex-start',
					padding: '0 0 92px 110px',
				}}
			>
				<div style={{display: 'flex', flexDirection: 'row', gap: 36}}>
					<div
						style={{
							width: 7,
							alignSelf: 'stretch',
							backgroundColor: OCHRE,
							borderRadius: 4,
							transform: `scaleY(${ruleGrow})`,
							transformOrigin: 'bottom',
						}}
					/>
					<div style={{display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 18}}>
						<div
							style={{
								...rise(0),
								backgroundColor: OCHRE_LIGHT,
								color: INDIGO,
								fontFamily: 'Inter',
								fontWeight: 700,
								fontSize: 23,
								letterSpacing: 2.6,
								padding: '9px 24px',
								borderRadius: 999,
							}}
						>
							{ch}
						</div>

						{ar ? (
							<div
								dir="rtl"
								lang="ar"
								style={{
									...rise(7),
									fontFamily: 'Amiri',
									fontWeight: 700,
									fontSize: arabicSize(ar),
									lineHeight: 1.7,
									color: INDIGO,
									// arabicSize already keeps the longest fragment inside the frame,
									// so hold each āyah on one line — a wrapped RTL line breaks left
									// and reads as though it were a separate phrase.
									whiteSpace: 'nowrap',
									textAlign: 'right',
								}}
							>
								{ar}
							</div>
						) : null}

						<div
							style={{
								...rise(ar ? 14 : 8),
								fontFamily: 'Inter',
								fontWeight: 700,
								fontSize: ar ? 42 : 82,
								letterSpacing: ar ? 3 : -0.5,
								color: ar ? SIENNA : INDIGO,
								maxWidth: 1560,
							}}
						>
							{head}
						</div>

						<div
							style={{
								...rise(ar ? 21 : 15),
								fontFamily: 'Inter',
								fontWeight: 400,
								fontSize: 35,
								color: SLATE,
								maxWidth: 1560,
							}}
						>
							{sub}
						</div>
					</div>
				</div>
			</AbsoluteFill>
		</AbsoluteFill>
	);
};
