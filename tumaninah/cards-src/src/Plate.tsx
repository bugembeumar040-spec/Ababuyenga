import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {useFonts} from './fonts';

export type PlateProps = {ar: string; gloss: string; ref: string; bg: string};

const INDIGO = '#2E3A56';
const OCHRE = '#C89A4A';
const SLATE = '#6B7280';
const SIENNA = '#A65A3A';

// The frames these sit on are empty illuminated cartouches — the pack left the
// interior blank so the āyah could be set here rather than generated into the
// art, where the script would have come out malformed.
const size = (ar: string) => {
	const n = ar.replace(/[ً-ْٰۖ-ۭ]/g, '').length;
	if (n <= 14) return 150;
	if (n <= 24) return 116;
	if (n <= 34) return 92;
	return 74;
};

export const Plate: React.FC<PlateProps> = ({ar, gloss, ref, bg}) => {
	useFonts();
	const frame = useCurrentFrame();
	const {durationInFrames} = useVideoConfig();

	const rise = (start: number) => {
		const p = interpolate(frame, [start, start + 20], [0, 1], {
			extrapolateLeft: 'clamp',
			extrapolateRight: 'clamp',
		});
		const e = 1 - Math.pow(1 - p, 3);
		return {opacity: e, transform: `translateY(${(1 - e) * 18}px)`};
	};
	const out = interpolate(frame, [durationInFrames - 18, durationInFrames - 1], [1, 0], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});
	const rule = interpolate(frame, [10, 34], [0, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});

	return (
		<AbsoluteFill style={{backgroundColor: bg, opacity: out}}>
			<AbsoluteFill style={{justifyContent: 'center', alignItems: 'center'}}>
				<div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 26}}>
					<div
						dir="rtl"
						lang="ar"
						style={{
							...rise(0),
							fontFamily: 'Amiri',
							fontWeight: 700,
							fontSize: size(ar),
							lineHeight: 1.65,
							color: INDIGO,
							whiteSpace: 'nowrap',
						}}
					>
						{ar}
					</div>
					<div
						style={{
							width: 300,
							height: 3,
							backgroundColor: OCHRE,
							borderRadius: 2,
							transform: `scaleX(${rule})`,
						}}
					/>
					<div
						style={{
							...rise(16),
							fontFamily: 'Inter',
							fontWeight: 400,
							fontSize: 38,
							// These sit on banners as well as cream cartouches, and slate on a
							// warm banner is too close in value to read. Indigo holds on both.
							color: INDIGO,
							maxWidth: 1300,
							textAlign: 'center',
						}}
					>
						{gloss}
					</div>
					<div
						style={{
							...rise(22),
							fontFamily: 'Inter',
							fontWeight: 700,
							fontSize: 21,
							letterSpacing: 3,
							color: SIENNA,
						}}
					>
						{ref}
					</div>
				</div>
			</AbsoluteFill>
		</AbsoluteFill>
	);
};
