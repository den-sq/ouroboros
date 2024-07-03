/// <reference types="vite-plugin-svgr/client" />
import SliceIcon from './assets/slice-icon.svg?react'
import SegmentIcon from './assets/segment-icon.svg?react'
import BackprojectIcon from './assets/backproject-icon.svg?react'
import MenuOption from './components/MenuOption/MenuOption'

function Menu(): JSX.Element {
	return (
		<div>
			<MenuOption optionName={'Slice'} icon={<SliceIcon />} active={true} />
			<MenuOption optionName={'Segment'} icon={<SegmentIcon />} />
			<MenuOption optionName={'Backproject'} icon={<BackprojectIcon />} />
		</div>
	)
}

export default Menu
