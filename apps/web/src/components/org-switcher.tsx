'use client';

import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu';

export function OrgSwitcher() {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={<Button variant='outline' className='w-[200px] justify-between' />}
      >
        <span className='truncate'>X Growth Hub</span>
      </DropdownMenuTrigger>
      <DropdownMenuContent className='w-[200px]' align='start'>
        <DropdownMenuLabel>Organization</DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuGroup>
          <DropdownMenuItem>X Growth Hub</DropdownMenuItem>
        </DropdownMenuGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
