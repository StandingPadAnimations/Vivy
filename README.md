# Vivy
My in-house fork of MCprep that gives more control to the user

> [!CAUTION]
> This version of Vivy is now discontinued, a new Vivy addon is planned.
>
> Check https://www.standingpad.org/posts/2024/05/plans-for-a-new-vivy-addon/ for more details

# Why?
I'm an MCprep maintainer, so it might seem strange that I would make a fork of MCprep, but hear me out for a bit.

MCprep is an amazing addon, and it has enabled the community to make Minecraft animations and renders in Blender. I wouldn't be here if it wasn't for MCprep.

However, MCprep's design goals are mainly to appeal to a less advanced userbase. There's nothing wrong with that, but it severely restricts its ability for advanced users. That's where Vivy comes in.

Vivy is a fork of MCprep, so any improvements MCprep has Vivy will gain, **but** Vivy aims to appeal to advanced users through control. MCprep doesn't give much control to the user, which is fine for most, but not all. Vivy aims to appeal to those that want more control.

## If you're an MCprep Maintainer, then why a fork?
The features Vivy aims to add would have one or more of the following issues:
- Not easy to turn into a simple UI 
- Creates issues for non-advanced users
- Too niche

As such, it's simply easier to make a fork, and implement those features in said fork; the stuff Vivy plans to do would clash with MCprep's design goals. Contrary to popular belief, forks don't mean all out war, and in this case are a win-win for all involved.

## So how does Vivy give more control?
Vivy gives more control through MCprep's material generation, which is perhaps the most used feature of MCprep. This is done by throwing out MCprep's old system (although it's still technically accessible) and replacing it with a system where users can define custom materials using a blend file and some JSON.

# Why the name Vivy?
It's based off of a light novel I got and I thought it was a nice name, hence the name Vivy for this project :D

# What license is Vivy under?
There are 2 parts to Vivy, the Vivy addon and [Vivy Components](https://github.com/StandingPadAnimations/Vivy-Components). The Vivy addon is what interacts with Blender, and is licensed under GPL. Vivy Components are what parse Vivy's JSON format, and is licensed under BSD 3-Clause. Vivy Components can also be used independently of Blender and could in theory be used to implement Vivy's system in other 3D programs.

The reason for this split is because I prefer to use more permissive licenses in the code I write, but MCprep and BPY (the Blender Python API) are GPL, and thus the Vivy addon has to be GPL as well.
