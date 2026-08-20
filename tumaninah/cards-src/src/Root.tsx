import React from 'react';
import {Composition} from 'remotion';
import {Card} from './Card';

export const RemotionRoot: React.FC = () => {
	return (
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
	);
};
