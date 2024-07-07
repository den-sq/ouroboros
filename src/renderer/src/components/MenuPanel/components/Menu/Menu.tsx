/// <reference types="vite-plugin-svgr/client" />
import SliceIcon from './assets/slice-icon.svg?react'
import SegmentIcon from './assets/segment-icon.svg?react'
import BackprojectIcon from './assets/backproject-icon.svg?react'
import MenuOption from './components/MenuOption/MenuOption'
import { useState } from 'react'

function Menu(): JSX.Element {
	const [active, setActive] = useState('Slice')

	return (
		<div>
			<MenuOption
				path={'/slice'}
				optionName={'Slice'}
				icon={<SliceIcon />}
				active={active}
				setActive={setActive}
			/>
			<MenuOption
				path={'/'}
				optionName={'Segment'}
				icon={<SegmentIcon />}
				active={active}
				setActive={setActive}
			/>
			<MenuOption
				path={'/backproject'}
				optionName={'Backproject'}
				icon={<BackprojectIcon />}
				active={active}
				setActive={setActive}
			/>
		</div>
	)
}

export default Menu
