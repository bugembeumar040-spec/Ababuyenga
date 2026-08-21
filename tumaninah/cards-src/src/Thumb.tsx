import React from 'react';
import {AbsoluteFill, Img, staticFile} from 'remotion';
import {useFonts} from './fonts';

const INDIGO = '#2E3A56';
const OCHRE = '#C89A4A';
const SIENNA = '#A65A3A';
const CREAM = '242, 237, 226';

// A thumbnail is read at about 210px wide in the sidebar, so everything here is
// sized for that: one Arabic word, one short line, and a single focal object.
export const Thumb: React.FC<{src: string; ar: string; line1: string; line2: string; ref: string}> =
({src, ar, line1, line2, ref}) => {
	useFonts();
	return (
		<AbsoluteFill style={{backgroundColor: '#F2EDE2'}}>
			{/* The glass sits centre in the source; push it right so the type has a side */}
			<Img
				src={staticFile(src)}
				style={{
					position: 'absolute',
					width: '104%',
					height: '104%',
					left: '38%',
					top: '-2%',
					objectFit: 'cover',
				}}
			/>
			<AbsoluteFill
				style={{
					background:
						`linear-gradient(to right, rgba(${CREAM},0.98) 0%, rgba(${CREAM},0.96) 48%,` +
						` rgba(${CREAM},0.72) 64%, rgba(${CREAM},0) 84%)`,
				}}
			/>
			<AbsoluteFill style={{justifyContent: 'center', padding: "0 0 0 114px"}}>
				<div style={{display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: 10, maxWidth: 930}}>
					<div dir="rtl" lang="ar" style={{
						fontFamily: 'Amiri', fontWeight: 700, fontSize: 156, lineHeight: 1.2,
						color: INDIGO, whiteSpace: 'nowrap',
					}}>{ar}</div>
					<div style={{width: 252, height: 10, backgroundColor: OCHRE, borderRadius: 4, margin: "33px 0 21px"}} />
					<div style={{fontFamily: 'Inter', fontWeight: 700, fontSize: 117, lineHeight: 1.04, color: INDIGO, letterSpacing: -1}}>
						{line1}
					</div>
					<div style={{fontFamily: 'Inter', fontWeight: 700, fontSize: 117, lineHeight: 1.04, color: SIENNA, letterSpacing: -1}}>
						{line2}
					</div>
					<div style={{fontFamily: 'Inter', fontWeight: 700, fontSize: 45, letterSpacing: 6, color: OCHRE, marginTop: 20}}>
						{ref}
					</div>
				</div>
			</AbsoluteFill>
		</AbsoluteFill>
	);
};
