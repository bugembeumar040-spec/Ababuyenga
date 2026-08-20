import {continueRender, delayRender, staticFile} from 'remotion';
import {useEffect, useState} from 'react';

const FACES: [string, number, string][] = [
	['Inter', 400, 'Inter-400.ttf'],
	['Inter', 500, 'Inter-500.ttf'],
	['Inter', 600, 'Inter-600.ttf'],
	['Inter', 700, 'Inter-700.ttf'],
	['Amiri', 400, 'Amiri-400.ttf'],
	['Amiri', 700, 'Amiri-700.ttf'],
];

// The card renders Arabic, so nothing may paint until the faces are actually
// resolved - a fallback frame would reshape the script wrongly.
export const useFonts = () => {
	const [handle] = useState(() => delayRender('loading fonts'));

	useEffect(() => {
		Promise.all(
			FACES.map(async ([family, weight, file]) => {
				const face = new FontFace(family, `url(${staticFile(`fonts/${file}`)})`, {
					weight: String(weight),
				});
				await face.load();
				document.fonts.add(face);
			}),
		)
			.then(() => document.fonts.ready)
			.then(() => continueRender(handle));
	}, [handle]);
};
