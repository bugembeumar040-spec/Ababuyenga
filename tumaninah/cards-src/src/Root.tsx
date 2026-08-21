import React from 'react';
import {Composition} from 'remotion';
import {Card} from './Card';
import {Plate} from './Plate';
import {Thumb} from './Thumb';

export const RemotionRoot: React.FC = () => {
	return (
		<>
		<Composition
			id="Card"
			component={Card}
			durationInFrames={180}
			fps={30}
			width={1920}
			height={1080}
			defaultProps={{
				ch: '1 · THE DISTURBANCE',
				ar: '',
				head: 'NAMED AFTER THUNDER',
				sub: 'The āyah on the wall lives inside a storm',
				bg: 'transparent',
			}}
		/>
		<Composition
			id="Plate"
			component={Plate}
			durationInFrames={180}
			fps={30}
			width={1920}
			height={1080}
			defaultProps={{
				ar: 'وَيُسَبِّحُ الرَّعْدُ بِحَمْدِهِ',
				gloss: 'And the thunder exalts Him with praise',
				ref: 'AR-RAʿD 13',
				bg: 'transparent',
			}}
		/>
		<Composition
			id="Thumb"
			component={Thumb}
			durationInFrames={1}
			fps={1}
			width={1920}
			height={1080}
			defaultProps={{
				src: 'thumb/glass.jpg',
				ar: 'طُمَأْنِينَة',
				struck: 'IT IS NOT “PEACE”',
				payoff: 'IT MEANS\nTO SETTLE',
				ref: 'AR-RAʿD',
				refBig: '28',
			}}
		/>
		</>
	);
};
