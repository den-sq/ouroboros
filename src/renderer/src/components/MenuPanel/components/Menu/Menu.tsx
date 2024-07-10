/// <reference types="vite-plugin-svgr/client" />
import SliceIcon from './assets/slice-icon.svg?react'
import BackprojectIcon from './assets/backproject-icon.svg?react'
import MenuOption from './components/MenuOption/MenuOption'
import { useLocation } from 'react-router-dom'

function Menu(): JSX.Element {
	const location = useLocation()

	return (
		<div>
			<MenuOption
				path={'/slice'}
				optionName={'Slice'}
				icon={<SliceIcon />}
				location={location}
			/>
			<MenuOption
				path={'/backproject'}
				optionName={'Backproject'}
				icon={<BackprojectIcon />}
				location={location}
			/>
		</div>
	)
}

export default Menu
